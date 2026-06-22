import os
import json
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import HumanMessage, AIMessage
from src.core.config import settings
from src.core.database import Base, engine, get_db, SessionLocal
from src.models.db_models import Transaction, Income, Budget, SavingsGoal, Account, Subscription, AuditLog, KnowledgeChunk, ChatMessage
from src.workflow.graph import get_graph_app
from src.tools.retrieval import generate_simple_embedding
from src.core.optimization import get_optimization_metrics
from src.observability.langsmith import get_observability_metrics, log_trace

app = FastAPI(
    title="Financial Health Advisor Agentic Platform",
    description="Production-ready multi-agent budget planning and wellness recommendation system.",
    version="1.0.0"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")
    
    # Auto-seed dummy data
    from src.core.seed import seed_data
    try:
        await seed_data()
    except Exception as e:
        print(f"Error seeding database on startup: {e}")

# --- Pydantic Schemas ---

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "user_1"
    thread_id: Optional[str] = None

class ApprovalRequest(BaseModel):
    thread_id: str
    approve: bool # True for approved, False for rejected
    user_id: Optional[str] = "user_1"

class BudgetUpdate(BaseModel):
    category: str
    limit: float

# --- Helper function for processing graph state ---

def format_graph_output(state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
    """Helper to convert graph state variables into client API response format."""
    return {
        "thread_id": thread_id,
        "status": "PAUSED_FOR_APPROVAL" if state.get("approval_required") else "COMPLETED",
        "intent": state.get("intent"),
        "risk_level": state.get("risk_level"),
        "active_agent": state.get("current_agent"),
        "plan": state.get("execution_plan"),
        "response": state.get("response"),
        "verification_status": state.get("verification_status"),
        "retries": state.get("retry_count", 0),
        "tool_calls": list(state.get("tool_results", {}).keys()),
        # Memory tracking
        "selected_memory_sources": state.get("selected_memory_sources"),
        "retrieved_memories": state.get("retrieved_memories"),
        "lessons_learned": state.get("lessons_learned")
    }

# --- FastAPI Router Endpoints ---

@app.post("/api/chat")
async def chat_endpoint(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Trigger the main LangGraph financial operations workflow.
    """
    thread_id = req.thread_id or str(uuid.uuid4())
    user_id = req.user_id or "user_1"
    config = {"configurable": {"thread_id": thread_id}}
    
    graph_app = get_graph_app()
    if not graph_app:
        raise HTTPException(status_code=500, detail="Graph app not initialized.")
        
    log_trace("query_received", {"query": req.query, "thread_id": thread_id, "user_id": user_id})
    
    # 1. Load existing messages from ChatMessage database table
    stmt = select(ChatMessage).where(
        ChatMessage.user_id == user_id,
        ChatMessage.thread_id == thread_id
    ).order_by(ChatMessage.timestamp)
    res = await db.execute(stmt)
    db_messages = res.scalars().all()
    
    graph_messages = []
    for msg in db_messages:
        if msg.role == "user":
            graph_messages.append(HumanMessage(content=msg.message))
        else:
            graph_messages.append(AIMessage(content=msg.message))
            
    # Append the new user query to the history passed to the graph
    graph_messages.append(HumanMessage(content=req.query))
    
    inputs = {
        "user_query": req.query,
        "messages": graph_messages,
        "retry_count": 0,
        "tool_results": {},
        "tools_to_call": [],
        "response": None,
        "approval_required": False,
        "approval_granted": False,
        "approval_action": None,
        "intent": None,
        "plan_steps": [],
        "current_step": 0,
        "execution_plan": None,
        "next_step": None,
        "verification_status": "PASSED",
        "user_id": user_id,
        "thread_id": thread_id,
        # Memory states
        "selected_memory_sources": None,
        "retrieved_memories": {},
        "lessons_learned": None
    }
    
    try:
        final_state = await graph_app.ainvoke(inputs, config)
        
        # 2. Save new query and response to ChatMessage table if completed or paused
        user_msg = ChatMessage(user_id=user_id, thread_id=thread_id, role="user", message=req.query)
        db.add(user_msg)
        
        resp_text = final_state.get("response")
        if resp_text:
            asst_msg = ChatMessage(user_id=user_id, thread_id=thread_id, role="assistant", message=resp_text)
            db.add(asst_msg)
            
        await db.commit()
        
        return format_graph_output(final_state, thread_id)
    except Exception as e:
        log_trace("execution_failed", {"reason": str(e)})
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

@app.post("/api/approve")
async def approve_endpoint(req: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    """
    Resume a workflow that has paused due to a human-in-the-loop approval gate.
    """
    config = {"configurable": {"thread_id": req.thread_id}}
    user_id = req.user_id or "user_1"
    
    graph_app = get_graph_app()
    if not graph_app:
        raise HTTPException(status_code=500, detail="Graph app not initialized.")
        
    # Retrieve current state from checkpointer
    state_desc = await graph_app.aget_state(config)
    if not state_desc or not state_desc.values:
        raise HTTPException(status_code=404, detail="Active execution thread not found.")
        
    current_values = state_desc.values
    if not current_values.get("approval_required"):
        raise HTTPException(status_code=400, detail="This thread is not currently awaiting approval.")
        
    # Update state values with approval selection
    updated_values = {
        "approval_granted": req.approve,
        "approval_action": "approved" if req.approve else "rejected",
        "approval_required": False
    }
    
    await graph_app.aupdate_state(config, updated_values, as_node="human_approval_node")
    
    # Resume the graph
    try:
        final_state = await graph_app.ainvoke(None, config)
        
        # Save assistant response if generated
        resp_text = final_state.get("response")
        if resp_text:
            asst_msg = ChatMessage(user_id=user_id, thread_id=req.thread_id, role="assistant", message=resp_text)
            db.add(asst_msg)
            await db.commit()
            
        return format_graph_output(final_state, req.thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume graph: {str(e)}")

@app.get("/api/history/{user_id}/{thread_id}")
async def get_thread_history(user_id: str, thread_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve chat history for a specific thread."""
    stmt = select(ChatMessage).where(
        ChatMessage.user_id == user_id,
        ChatMessage.thread_id == thread_id
    ).order_by(ChatMessage.timestamp)
    res = await db.execute(stmt)
    messages = res.scalars().all()
    return [
        {
            "role": m.role,
            "content": m.message,
            "timestamp": m.timestamp.isoformat()
        }
        for m in messages
    ]

@app.get("/api/threads/{user_id}")
async def get_user_threads(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve list of unique threads and their titles for a user."""
    stmt = select(ChatMessage.thread_id).where(ChatMessage.user_id == user_id).distinct()
    res = await db.execute(stmt)
    threads = res.scalars().all()
    
    thread_list = []
    for tid in threads:
        title_stmt = select(ChatMessage.message).where(
            ChatMessage.user_id == user_id,
            ChatMessage.thread_id == tid
        ).order_by(ChatMessage.timestamp).limit(1)
        title_res = await db.execute(title_stmt)
        first_msg = title_res.scalar_one_or_none() or "Empty Thread"
        thread_list.append({
            "thread_id": tid,
            "title": first_msg[:60] + "..." if len(first_msg) > 60 else first_msg
        })
    return thread_list


@app.post("/api/rag/upload")
async def upload_rag_document(
    document_name: str = Form(...),
    file: UploadFile = File(None),
    raw_text: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest text content or uploaded files (PDF, CSV, TXT),
    chunks them, computes deterministic similarity embeddings,
    and inserts them into the SQLite database.
    """
    content = ""
    if file:
        file_bytes = await file.read()
        content = file_bytes.decode("utf-8", errors="ignore")
    elif raw_text:
        content = raw_text
    else:
        raise HTTPException(status_code=400, detail="Provide either a file upload or raw_text.")
        
    if not content.strip():
        raise HTTPException(status_code=400, detail="Document content is empty.")
        
    chunk_size = 500
    overlap = 50
    chunks = []
    
    start = 0
    while start < len(content):
        chunk = content[start : start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap
        
    for i, chunk_text in enumerate(chunks):
        vector = generate_simple_embedding(chunk_text)
        vector_str = json.dumps(vector)
        
        chunk_obj = KnowledgeChunk(
            document_name=document_name,
            content=chunk_text,
            metadata_json=json.dumps({"chunk_index": i, "total_chunks": len(chunks)}),
            embedding=vector_str
        )
        db.add(chunk_obj)
        
    await db.commit()
    return {
        "status": "success",
        "document_name": document_name,
        "chunks_indexed": len(chunks)
    }

@app.get("/api/metrics")
async def get_metrics():
    """
    Fetch cumulative metrics from model runs, latencies, success rates, retry rates, and cache hits.
    """
    telemetry = get_observability_metrics()
    cache_stats = get_optimization_metrics()
    
    telemetry.update({
        "cache_hits": cache_stats.get("cache_hits", 0),
        "tokens_saved": cache_stats.get("tokens_saved", 0),
        "context_reduction_percentage": round(cache_stats.get("context_reduction_percentage", 0.0), 2)
    })
    return telemetry

@app.get("/api/audit-logs")
async def get_audit_logs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
    Read latest system audit logs representing safety guardrail violations and actions.
    """
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    
    return [
        {
            "log_id": l.log_id,
            "timestamp": l.timestamp.isoformat(),
            "action": l.action,
            "agent": l.agent,
            "status": l.status,
            "details": l.details
        }
        for l in logs
    ]

# --- Finance REST Endpoints ---

@app.get("/api/dashboard")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Unified endpoint to return aggregate financial information for the front-end dashboard."""
    acc_stmt = select(Account)
    acc_res = await db.execute(acc_stmt)
    accounts = acc_res.scalars().all()
    
    budget_stmt = select(Budget)
    budget_res = await db.execute(budget_stmt)
    budgets = budget_res.scalars().all()
    
    goals_stmt = select(SavingsGoal)
    goals_res = await db.execute(goals_stmt)
    goals = goals_res.scalars().all()
    
    subs_stmt = select(Subscription)
    subs_res = await db.execute(subs_stmt)
    subscriptions = subs_res.scalars().all()
    
    total_net_worth = sum(a.balance for a in accounts)
    
    return {
        "net_worth": total_net_worth,
        "accounts": [{"account_name": a.account_name, "account_type": a.account_type, "balance": a.balance} for a in accounts],
        "budgets": {b.category: b.budget_amount for b in budgets},
        "goals": [{"goal_name": g.goal_name, "target_amount": g.target_amount, "current_saved": g.current_saved, "target_date": g.target_date} for g in goals],
        "subscriptions": [{"merchant": s.merchant, "amount": s.amount, "frequency": s.frequency, "is_used": s.is_used} for s in subscriptions]
    }

@app.get("/api/transactions")
async def get_transactions(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetch recent transaction ledger rows."""
    stmt = select(Transaction).order_by(desc(Transaction.date)).limit(limit)
    res = await db.execute(stmt)
    txns = res.scalars().all()
    return [
        {
            "transaction_id": t.transaction_id,
            "date": t.date,
            "merchant": t.merchant,
            "amount": t.amount,
            "account_type": t.account_type,
            "description": t.description,
            "category": t.category,
            "is_subscription": t.is_subscription
        }
        for t in txns
    ]

@app.post("/api/budgets")
async def create_or_update_budget(b: BudgetUpdate, db: AsyncSession = Depends(get_db)):
    """REST endpoint to create or update budget limits."""
    stmt = select(Budget).where(Budget.category.ilike(b.category))
    res = await db.execute(stmt)
    budget = res.scalar_one_or_none()
    
    if budget:
        old_val = budget.budget_amount
        budget.budget_amount = b.limit
        details = f"Updated budget limit for {b.category} from ₹{old_val} to ₹{b.limit}"
    else:
        budget = Budget(category=b.category, budget_amount=b.limit)
        db.add(budget)
        details = f"Created new budget limit for {b.category} set to ₹{b.limit}"
        
    await db.flush()
    audit = AuditLog(
        action="REST_BUDGET_CHANGE",
        agent="api_server",
        status="SUCCESS",
        details=details
    )
    db.add(audit)
    await db.commit()
    
    return {"category": budget.category, "budget_limit": budget.budget_amount}
