import re
import os
from typing import Dict, Any, List
import pdfplumber
import fitz  # PyMuPDF

def parse_transactions_from_text(text: str) -> List[Dict[str, Any]]:
    """Helper regex to parse transactions from credit card or bank statement text."""
    # Pattern to match: Date (YYYY-MM-DD or DD-MM-YYYY or DD/MM/YYYY), Merchant, Amount
    # Example: 2026-06-01 Swiggy 450.00
    # Example: 10/06/2026 Amazon ₹4,500.00
    lines = text.split("\n")
    transactions = []
    
    # Simple regex pattern: Date, merchant (non-digit words), amount (decimal)
    pattern = re.compile(
        r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\s+"  # Date
        r"([A-Za-z0-9\s&\.\*]+?)\s+"                             # Merchant
        r"(?:Rs\.?|₹)?\s*([\d,]+\.?\d*)"                         # Amount
    )
    
    for i, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            date_str = match.group(1).replace("/", "-")
            merchant = match.group(2).strip()
            amount_str = match.group(3).replace(",", "")
            
            # Simple standard YYYY-MM-DD check
            # If date is DD-MM-YYYY, convert to YYYY-MM-DD
            if len(date_str) == 10 and date_str[2] == "-":
                parts = date_str.split("-")
                date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
                
            try:
                amount = float(amount_str)
                transactions.append({
                    "transaction_id": f"EXT{i:03d}",
                    "date": date_str,
                    "merchant": merchant,
                    "amount": amount,
                    "account_type": "Credit Card",
                    "description": line.strip(),
                    "category": "Unassigned"
                })
            except ValueError:
                continue
                
    return transactions

async def process_bank_statement_text_tool(raw_text: str) -> Dict[str, Any]:
    """Processes raw bank/card statement text and extracts transaction items."""
    try:
        txns = parse_transactions_from_text(raw_text)
        return {
            "status": "success",
            "data": {
                "transactions": txns,
                "parsed_count": len(txns)
            },
            "metadata": {"processor": "statement_text_processor"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def process_pdf_statement_tool(file_path: str) -> Dict[str, Any]:
    """
    Extracts text from a bank statement PDF using pdfplumber/PyMuPDF, 
    then parses transaction items.
    """
    try:
        if not os.path.exists(file_path):
            return {
                "status": "failed",
                "data": {},
                "metadata": {"error": f"File not found: {file_path}"}
            }
            
        text = ""
        # 1. Try PyMuPDF
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception:
            # 2. Fall back to pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        txns = parse_transactions_from_text(text)
        return {
            "status": "success",
            "data": {
                "file_path": file_path,
                "transactions": txns,
                "parsed_count": len(txns)
            },
            "metadata": {"processor": "pdf_statement_processor"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }
