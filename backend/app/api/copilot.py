from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from api.auth import get_current_user
from schemas.chat import ChatRequest, ApprovalRequest
from services.langgraph_service import LanggraphService
from services.chat_service import ChatService
from models.session import Session
from sqlalchemy import select

router = APIRouter(prefix="/copilot", tags=["Copilot"])

@router.get("/history")
async def get_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_svc = ChatService(db)
    user_id = current_user["user_id"]
    
    # Get latest active thread for user
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if not sess:
        return []
        
    return await chat_svc.get_thread_history(user_id, sess.session_id)

@router.get("/status")
async def get_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user["user_id"]
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if not sess:
        return {"status": "COMPLETED"}
        
    from src.workflow.graph import get_graph_app
    graph_app = get_graph_app()
    if not graph_app:
        return {"status": "COMPLETED"}
        
    config = {"configurable": {"thread_id": sess.session_id}}
    state_desc = await graph_app.aget_state(config)
    
    if state_desc and state_desc.values and state_desc.values.get("approval_required"):
        return {"status": "PAUSED_FOR_APPROVAL"}
        
    return {"status": "COMPLETED"}


@router.post("/chat")
async def chat(
    req: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    lang_svc = LanggraphService(db)
    user_id = current_user["user_id"]
    
    # Find latest active session or create new one
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if sess:
        thread_id = sess.session_id
    else:
        import uuid
        thread_id = str(uuid.uuid4())
        # Create session record
        sess = Session(session_id=thread_id, user_id=user_id)
        db.add(sess)
        await db.flush()
        
    try:
        # Update session timestamp
        sess.updated_at = sess.updated_at # triggers onupdate
        res_data = await lang_svc.invoke_chat(req.message, user_id, thread_id)
        await db.commit()
        return res_data
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve")
async def approve(
    req: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    lang_svc = LanggraphService(db)
    user_id = current_user["user_id"]
    
    # Get latest active session for thread_id
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if not sess:
        raise HTTPException(status_code=404, detail="No active session found for user.")
        
    try:
        res_data = await lang_svc.approve_action(sess.session_id, req.approve, user_id)
        await db.commit()
        return res_data
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
