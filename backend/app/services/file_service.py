import os
import csv
import uuid
import io
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.uploaded_file import UploadedFile
from src.models.db_models import Transaction, Account, AuditLog
from src.tools.processing import process_pdf_statement_tool, process_bank_statement_text_tool

class FileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_statement(self, filename: str, content: bytes, account_name: str, account_type: str) -> Dict[str, Any]:
        # 1. Save uploaded file record
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploaded_statements")
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, f"{uuid.uuid4()}_{filename}")
        with open(filepath, "wb") as f:
            f.write(content)
            
        file_record = UploadedFile(filename=filename, filepath=filepath)
        self.db.add(file_record)
        await self.db.flush()
        
        # 2. Extract transactions based on file extension
        extracted_txns = []
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".pdf":
            # Call PDF tool
            res = await process_pdf_statement_tool(filepath)
            if res.get("status") == "success":
                extracted_txns = res["data"].get("transactions", [])
        elif ext == ".csv":
            # Try parsing as CSV structure first
            try:
                text_content = content.decode("utf-8", errors="ignore")
                f_io = io.StringIO(text_content)
                reader = csv.DictReader(f_io)
                
                # Check if headers look like transaction headers
                headers = [h.lower() for h in (reader.fieldnames or [])]
                if any(h in headers for h in ["amount", "value", "merchant", "description"]):
                    # Maps headers dynamically
                    amount_col = next((h for h in reader.fieldnames if h.lower() in ["amount", "value", "amt"]), "amount")
                    date_col = next((h for h in reader.fieldnames if h.lower() in ["date", "txn_date", "date_time"]), "date")
                    merchant_col = next((h for h in reader.fieldnames if h.lower() in ["merchant", "payee", "shop"]), "merchant")
                    desc_col = next((h for h in reader.fieldnames if h.lower() in ["description", "narrative", "details"]), "description")
                    category_col = next((h for h in reader.fieldnames if h.lower() in ["category", "type"]), "category")
                    
                    for i, row in enumerate(reader):
                        try:
                            # Safely extract
                            amt = float(row.get(amount_col, "0").replace(",", ""))
                            dt = row.get(date_col, "")
                            merch = row.get(merchant_col, "")
                            desc = row.get(desc_col, "")
                            cat = row.get(category_col, "Shopping")
                            
                            # Standardize fields
                            extracted_txns.append({
                                "transaction_id": f"CSV{uuid.uuid4().hex[:6].upper()}{i:02d}",
                                "date": dt,
                                "merchant": merch or "Generic Merchant",
                                "amount": amt,
                                "account_type": account_type,
                                "description": desc or f"Transaction from {filename}",
                                "category": cat or "Shopping"
                            })
                        except Exception:
                            continue
                else:
                    # Fallback to simple text parser tool
                    res = await process_bank_statement_text_tool(text_content)
                    if res.get("status") == "success":
                        extracted_txns = res["data"].get("transactions", [])
            except Exception:
                pass
        else:
            # Try raw text parsing tool
            try:
                text_content = content.decode("utf-8", errors="ignore")
                res = await process_bank_statement_text_tool(text_content)
                if res.get("status") == "success":
                    extracted_txns = res["data"].get("transactions", [])
            except Exception:
                pass

        # 3. Seed parsed transactions to database
        added_count = 0
        total_debit_amount = 0.0
        
        for tx in extracted_txns:
            # Check if transaction_id already exists to prevent duplicate ingestion
            stmt = select(Transaction).where(Transaction.transaction_id == tx["transaction_id"])
            existing_res = await self.db.execute(stmt)
            if existing_res.scalar_one_or_none():
                continue
                
            txn_obj = Transaction(
                transaction_id=tx["transaction_id"],
                date=tx["date"],
                merchant=tx["merchant"],
                amount=tx["amount"],
                account_type=account_type,
                description=tx["description"],
                category=tx.get("category", "Unassigned"),
                is_subscription=False
            )
            self.db.add(txn_obj)
            added_count += 1
            total_debit_amount += tx["amount"]

        # 4. Update the account balance
        if added_count > 0:
            stmt = select(Account).where(Account.account_name == account_name)
            res = await self.db.execute(stmt)
            acc = res.scalar_one_or_none()
            
            if acc:
                acc.balance -= total_debit_amount
            else:
                acc = Account(account_name=account_name, account_type=account_type, balance=-total_debit_amount)
                self.db.add(acc)
                
            audit = AuditLog(
                action="STATEMENT_INGESTION",
                agent="file_service",
                status="SUCCESS",
                details=f"Ingested statement {filename}. Added {added_count} transactions. Updated balance for {account_name}."
            )
            self.db.add(audit)
            await self.db.commit()

        return {
            "message": f"Successfully parsed and ingested {added_count} transaction entries from statement.",
            "parsed_count": len(extracted_txns),
            "added_count": added_count,
            "total_value": total_debit_amount
        }
