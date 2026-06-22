import uuid
import time
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.workflow.graph import get_graph_app
from src.models.db_models import ChatMessage, AuditLog
from utils.helpers import log_conversation_csv, log_agent_action_csv, log_usage_stats_csv
from src.core.optimization import get_optimization_metrics
from src.observability.langsmith import get_observability_metrics

class LanggraphService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def format_graph_output(self, state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """Convert graph state into a structured client API response."""
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

    async def invoke_chat(self, query: str, user_id: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        thread_id = thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        graph_app = get_graph_app()
        if not graph_app:
            raise Exception("LangGraph Application not initialized.")
            
        # 1. Load history from ChatMessage table
        stmt = select(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.timestamp)
        res = await self.db.execute(stmt)
        db_messages = res.scalars().all()
        
        graph_messages = []
        for msg in db_messages:
            if msg.role == "user":
                graph_messages.append(HumanMessage(content=msg.message))
            else:
                graph_messages.append(AIMessage(content=msg.message))
                
        graph_messages.append(HumanMessage(content=query))
        
        inputs = {
            "user_query": query,
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
        
        # Invoke LangGraph
        final_state = await graph_app.ainvoke(inputs, config)
        
        # Save user message
        user_msg = ChatMessage(user_id=user_id, thread_id=thread_id, role="user", message=query)
        self.db.add(user_msg)
        
        resp_text = final_state.get("response")
        if resp_text:
            asst_msg = ChatMessage(user_id=user_id, thread_id=thread_id, role="assistant", message=resp_text)
            self.db.add(asst_msg)
            
        await self.db.commit()
        
        # CSV and Log telemetry
        latency = time.time() - start_time
        cache_stats = get_optimization_metrics()
        
        log_conversation_csv(user_id, thread_id, query, resp_text or "[Awaiting Approval]")
        log_agent_action_csv(
            action="CHAT_INVOCATION",
            agent=final_state.get("current_agent") or "supervisor",
            status="SUCCESS" if not final_state.get("approval_required") else "PAUSED",
            details=f"Query: {query[:50]}... Latency: {latency:.2f}s"
        )
        log_usage_stats_csv(user_id, latency, cache_stats.get("cache_hits", 0), cache_stats.get("tokens_saved", 0))
        
        return self.format_graph_output(final_state, thread_id)

    async def approve_action(self, thread_id: str, approve: bool, user_id: str) -> Dict[str, Any]:
        start_time = time.time()
        config = {"configurable": {"thread_id": thread_id}}
        
        graph_app = get_graph_app()
        if not graph_app:
            raise Exception("LangGraph Application not initialized.")
            
        state_desc = await graph_app.aget_state(config)
        if not state_desc or not state_desc.values:
            raise Exception("Active thread not found.")
            
        current_values = state_desc.values
        if not current_values.get("approval_required"):
            raise Exception("This thread is not currently awaiting approval.")
            
        updated_values = {
            "approval_granted": approve,
            "approval_action": "approved" if approve else "rejected",
            "approval_required": False
        }
        
        await graph_app.aupdate_state(config, updated_values, as_node="human_approval_node")
        
        # Resume the graph
        final_state = await graph_app.ainvoke(None, config)
        
        resp_text = final_state.get("response")
        if resp_text:
            asst_msg = ChatMessage(user_id=user_id, thread_id=thread_id, role="assistant", message=resp_text)
            self.db.add(asst_msg)
            
        # Add audit log for approval
        audit = AuditLog(
            action="HUMAN_APPROVAL_RESPONSE",
            agent="human_supervisor",
            status="PASSED" if approve else "BLOCKED",
            details=f"Action: {'Approved' if approve else 'Rejected'} for thread {thread_id}."
        )
        self.db.add(audit)
        await self.db.commit()
        
        # CSV and Log telemetry
        latency = time.time() - start_time
        cache_stats = get_optimization_metrics()
        
        log_conversation_csv(user_id, thread_id, f"[APPROVAL RESPONSE: {approve}]", resp_text or "")
        log_agent_action_csv(
            action="HUMAN_APPROVAL",
            agent="human_supervisor",
            status="PASSED" if approve else "BLOCKED",
            details=f"Thread: {thread_id} approved: {approve}"
        )
        log_usage_stats_csv(user_id, latency, cache_stats.get("cache_hits", 0), cache_stats.get("tokens_saved", 0))
        
        return self.format_graph_output(final_state, thread_id)
