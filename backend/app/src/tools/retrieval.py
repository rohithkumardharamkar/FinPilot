import json
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Transaction, Income, Budget, SavingsGoal, Account, KnowledgeChunk

def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Helper to calculate cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_prod = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    if magnitude1 == 0.0 or magnitude2 == 0.0:
        return 0.0
    return dot_prod / (magnitude1 * magnitude2)

def generate_simple_embedding(text: str) -> List[float]:
    """
    Generate a simple deterministic 128-dimension text embedding vector.
    Enables offline vector search simulation in SQLite without calling external APIs.
    """
    cleaned = text.lower()
    dimensions = 128
    vector = [0.0] * dimensions
    for i, char in enumerate(cleaned):
        idx = (ord(char) * (i + 1)) % dimensions
        vector[idx] += 1.0
    magnitude = sum(x * x for x in vector) ** 0.5
    if magnitude > 0.0:
        vector = [x / magnitude for x in vector]
    return vector

async def aggregate_accounts_tool(db: AsyncSession) -> Dict[str, Any]:
    """
    Multi-Account Aggregator: Collect accounts and current balances.
    Returns: Unified ledger overview.
    """
    try:
        stmt = select(Account)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        
        acc_data = []
        total_net_worth = 0.0
        for acc in accounts:
            acc_data.append({
                "account_name": acc.account_name,
                "account_type": acc.account_type,
                "balance": acc.balance
            })
            total_net_worth += acc.balance
            
        return {
            "status": "success",
            "data": {
                "accounts": acc_data,
                "total_net_worth": total_net_worth
            },
            "metadata": {"count": len(acc_data)}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def retrieve_transactions_tool(db: AsyncSession) -> Dict[str, Any]:
    """Retrieve all transactions for unified ledger analysis."""
    try:
        stmt = select(Transaction).order_by(Transaction.date)
        result = await db.execute(stmt)
        txns = result.scalars().all()
        
        data_list = []
        for t in txns:
            data_list.append({
                "transaction_id": t.transaction_id,
                "date": t.date,
                "merchant": t.merchant,
                "amount": t.amount,
                "account_type": t.account_type,
                "description": t.description,
                "category": t.category,
                "is_subscription": t.is_subscription
            })
            
        return {
            "status": "success",
            "data": {"transactions": data_list},
            "metadata": {"count": len(data_list)}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def retrieve_income_tool(db: AsyncSession) -> Dict[str, Any]:
    """Retrieve salary and other income details."""
    try:
        stmt = select(Income)
        result = await db.execute(stmt)
        income_row = result.scalars().first()
        
        if not income_row:
            return {
                "status": "success",
                "data": {"salary": 0.0, "other_income": 0.0, "total_income": 0.0},
                "metadata": {"source": "default"}
            }
            
        return {
            "status": "success",
            "data": {
                "salary": income_row.salary,
                "other_income": income_row.other_income,
                "total_income": income_row.salary + income_row.other_income
            },
            "metadata": {"source": "database"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def retrieve_budgets_tool(db: AsyncSession) -> Dict[str, Any]:
    """Retrieve all budget limits."""
    try:
        stmt = select(Budget)
        result = await db.execute(stmt)
        budgets = result.scalars().all()
        
        data = {b.category: b.budget_amount for b in budgets}
        return {
            "status": "success",
            "data": {"budgets": data},
            "metadata": {"count": len(data)}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def retrieve_savings_goals_tool(db: AsyncSession) -> Dict[str, Any]:
    """Retrieve savings goals progress."""
    try:
        stmt = select(SavingsGoal)
        result = await db.execute(stmt)
        goals = result.scalars().all()
        
        data_list = []
        for g in goals:
            data_list.append({
                "goal_name": g.goal_name,
                "target_amount": g.target_amount,
                "current_saved": g.current_saved,
                "target_date": g.target_date,
                "progress_percentage": round((g.current_saved / g.target_amount) * 100.0, 2) if g.target_amount > 0 else 0.0
            })
            
        return {
            "status": "success",
            "data": {"goals": data_list},
            "metadata": {"count": len(data_list)}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }

async def retrieve_rag_knowledge_tool(query: str, db: AsyncSession) -> Dict[str, Any]:
    """
    RAG Tool retrieving top 5 chunks matching the query using cosine similarity.
    Supports offline vector calculations in SQLite.
    """
    try:
        query_vector = generate_simple_embedding(query)
        
        stmt = select(KnowledgeChunk)
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        
        scored_chunks = []
        for chunk in chunks:
            try:
                chunk_vector = json.loads(chunk.embedding)
            except Exception:
                chunk_vector = [float(x) for x in chunk.embedding.split(",")] if "," in chunk.embedding else []
                
            similarity = compute_cosine_similarity(query_vector, chunk_vector)
            
            # Simple keyword boost for exact match to strengthen reranking
            keywords = query.lower().split()
            content_lower = chunk.content.lower()
            keyword_matches = sum(1 for kw in keywords if kw in content_lower)
            if len(keywords) > 0:
                similarity += 0.1 * (keyword_matches / len(keywords))
                
            scored_chunks.append((similarity, chunk))
            
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:5]
        
        results_data = []
        for score, chunk in top_chunks:
            meta = json.loads(chunk.metadata_json) if chunk.metadata_json else {}
            results_data.append({
                "chunk_id": chunk.chunk_id,
                "document_name": chunk.document_name,
                "content": chunk.content,
                "similarity_score": round(score, 4),
                "metadata": meta
            })
            
        return {
            "status": "success",
            "data": {"results": results_data},
            "metadata": {
                "query": query,
                "total_db_chunks": len(chunks),
                "retrieved_count": len(results_data)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "metadata": {"error": str(e)}
        }
