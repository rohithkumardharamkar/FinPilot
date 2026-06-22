from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.tools.retrieval import generate_simple_embedding, compute_cosine_similarity
from src.models.db_models import Transaction, Budget, SavingsGoal, Subscription

# Global memory cache for vector chunks
_cached_vectors: List[Dict[str, Any]] = []

async def create_embeddings(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Parse database records, construct text records, compute their embeddings,
    and cache them for similarity search.
    """
    global _cached_vectors
    _cached_vectors = []
    
    # 1. Transaction Embeddings
    result = await db.execute(select(Transaction))
    txns = result.scalars().all()
    for t in txns:
        text = f"Transaction (ID: {t.transaction_id}): Spent ₹{t.amount} at {t.merchant} on {t.date} via {t.account_type}. Description: {t.description}. Category: {t.category}."
        _cached_vectors.append({
            "text": text,
            "embedding": generate_simple_embedding(text),
            "source": "transaction",
            "patient_id": 1,
            "patient_name": "User"
        })
                
    # 2. Budget Embeddings
    result = await db.execute(select(Budget))
    budgets = result.scalars().all()
    for b in budgets:
        text = f"Budget limit for category '{b.category}': ₹{b.budget_amount}."
        _cached_vectors.append({
            "text": text,
            "embedding": generate_simple_embedding(text),
            "source": "budget",
            "patient_id": 1,
            "patient_name": "User"
        })
                
    # 3. Savings Goal Embeddings
    result = await db.execute(select(SavingsGoal))
    goals = result.scalars().all()
    for g in goals:
        text = f"Savings goal '{g.goal_name}': Target ₹{g.target_amount}, currently saved ₹{g.current_saved}. Target date: {g.target_date}."
        _cached_vectors.append({
            "text": text,
            "embedding": generate_simple_embedding(text),
            "source": "savings_goal",
            "patient_id": 1,
            "patient_name": "User"
        })
                
    # 4. Subscription Embeddings
    result = await db.execute(select(Subscription))
    subs = result.scalars().all()
    for s in subs:
        status_str = "active" if s.is_used else "inactive/cancelled"
        text = f"Subscription to {s.merchant}: Cost ₹{s.amount} billed {s.frequency}. Is currently {status_str}."
        _cached_vectors.append({
            "text": text,
            "embedding": generate_simple_embedding(text),
            "source": "subscription",
            "patient_id": 1,
            "patient_name": "User"
        })
                
    return _cached_vectors

async def semantic_search(query: str, db: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search vector cache for similarities.
    If cache is empty, runs create_embeddings() first.
    """
    global _cached_vectors
    if not _cached_vectors:
        await create_embeddings(db)
        
    query_vector = generate_simple_embedding(query)
    scored = []
    
    for item in _cached_vectors:
        similarity = compute_cosine_similarity(query_vector, item["embedding"])
        
        keywords = query.lower().split()
        item_text_lower = item["text"].lower()
        match_count = sum(1 for kw in keywords if kw in item_text_lower)
        if keywords:
            similarity += 0.15 * (match_count / len(keywords))
            
        scored.append((similarity, item))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, item in scored[:limit]:
        results.append({
            "text": item["text"],
            "content": item["text"],
            "document_name": item["source"],
            "patient_id": item["patient_id"],
            "patient_name": item["patient_name"],
            "source": item["source"],
            "similarity_score": round(score, 4)
        })
    return results

async def retrieve_relevant_context(query: str, db: AsyncSession) -> str:
    """Retrieve top similarities formatted as a clean reference string."""
    results = await semantic_search(query, db, limit=3)
    if not results:
        return "No relevant vector memory context found."
        
    context_lines = []
    for r in results:
        context_lines.append(f"- [{r['source'].upper()}] (Score: {r['similarity_score']}): {r['text']}")
    return "\n".join(context_lines)
