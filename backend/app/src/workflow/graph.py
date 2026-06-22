import json
import sqlite3
import re
import asyncio
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from src.agents.state import AgentState
from src.core.database import SessionLocal
from src.core.guardrails import run_guardrails, validate_input, validate_output
from src.agents.supervisor import run_supervisor_agent
from src.agents.planner import run_planner_agent
from src.agents.specialist import (
    run_financial_analysis_agent,
    run_spending_analysis_agent,
    run_pattern_detection_agent,
    run_reporting_agent,
    run_email_agent,
    run_recommendation_agent,
    run_memory_agent
)
from src.agents.verification import (
    verify_layer1_tools,
    verify_layer2_agent,
    verify_layer3_e2e
)
from src.core.optimization import (
    compress_context_tool,
    get_cached_tool_result,
    set_cached_tool_result,
    get_optimization_metrics
)
from src.observability.langsmith import log_trace, accumulate_metrics, get_observability_metrics

# Tools
from src.tools.retrieval import (
    aggregate_accounts_tool,
    retrieve_transactions_tool,
    retrieve_income_tool,
    retrieve_budgets_tool,
    retrieve_savings_goals_tool,
    retrieve_rag_knowledge_tool
)
from src.tools.processing import (
    process_bank_statement_text_tool,
    process_pdf_statement_tool
)
from src.tools.execution import (
    cancel_subscription_tool,
    update_budget_tool,
    transfer_savings_tool,
    send_email_report_tool
)
from src.tools.analysis import (
    analyze_spending_patterns_tool,
    forecast_month_end_tool,
    detect_anomalies_tool
)
from src.tools.verification import (
    data_verification_tool,
    financial_rules_verification_tool,
    workflow_verification_tool
)
from src.tools.reporting import (
    track_budget_variance_tool,
    track_savings_goals_tool,
    calculate_wellness_score_tool,
    generate_financial_report_tool,
    audit_report_tool
)
from src.agents.router import call_model
from src.core.config import settings

# Memory
from src.memory.entity_memory import (
    get_financial_profile,
    get_budget_limits,
    get_savings_goals,
    get_active_subscriptions,
    get_user_entities,
    save_user_entity
)
from src.memory.episodic_memory import (
    get_transaction_timeline,
    get_recent_transactions,
    get_episodic_memories,
    save_episodic_memory
)
from src.memory.summary_memory import retrieve_summary, check_and_trigger_summarization
from src.memory.reflection_memory import store_reflection, retrieve_lessons
from src.memory.goal_memory import get_goals, save_goal
from src.memory.preference_memory import get_preferences, save_preference
from src.memory.vector_memory import retrieve_relevant_context



# --- LangGraph Nodes ---

async def input_validation_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "InputValidationNode"})
    query = state.get("user_query", "").strip()
    if not query:
        return {
            "response": "Please provide a valid query.",
            "next_step": "response"
        }
        
    # Greeting Detection
    greeting_pattern = re.compile(
        r"^(hello|hi|hey|greetings|good\s+morning|good\s+afternoon|good\s+evening|yo|hiya|dear\s+agent)(\s+.*)?$",
        re.IGNORECASE
    )
    if greeting_pattern.match(query):
        return {
            "response": "Hello! I am your Lead Financial Wellness Advisor. How can I help you with your budget, savings, or subscriptions today?",
            "intent": "greeting",
            "risk_level": "low",
            "next_step": "response"
        }
        
    # Input Guardrails (PII / Off-Topic detection)
    try:
        validate_input(query)
    except ValueError as e:
        error_msg = str(e)
        log_trace("input_guardrail_blocked", {"reason": error_msg})
        if "Query restricted" in error_msg or "off-topic" in error_msg.lower():
            response_text = "I am a financial agent. I support budget planning, expense tracking, and financial wellness queries only."
        elif "Blocked input" in error_msg:
            response_text = f"Blocked input detected: {error_msg}"
        else:
            response_text = error_msg
        return {
            "response": response_text,
            "next_step": "response"
        }
        
    # Security/Jailbreak Guardrails
    async with SessionLocal() as db:
        guard_res = await run_guardrails(query, db)
        
    if not guard_res.allowed:
        log_trace("guardrail_violation", {"action": guard_res.action, "details": guard_res.details})
        from src.core.email import send_email
        send_email(
            subject=f"SECURITY ALERT: {guard_res.action}",
            body=f"A security violation was blocked by the guardrail system.\n\nQuery: {query}\nAction: {guard_res.action}\nDetails: {guard_res.details}"
        )
        return {
            "response": guard_res.details,
            "next_step": "response"
        }
        
    return {
        "user_query": guard_res.masked_text,
        "next_step": "memory_retrieval"
    }


async def memory_retrieval_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "MemoryRetrievalNode"})
    user_id = state.get("user_id") or "user_1"
    
    async with SessionLocal() as db:
        summary = await retrieve_summary(user_id, db)
        entities = await get_user_entities(user_id, db)
        profile = await get_financial_profile(db, user_id)
        budgets = await get_budget_limits(db, user_id)
        goals_db = await get_savings_goals(db, user_id)
        subscriptions = await get_active_subscriptions(db, user_id)
        goals = await get_goals(user_id, db)
        preferences = await get_preferences(user_id, db)
        episodic = await get_episodic_memories(user_id, db)
        timeline = await get_transaction_timeline(db, user_id)
        vector_context = await retrieve_relevant_context(state["user_query"], db)
        lessons = await retrieve_lessons(user_id, db)
        
    lessons_str = "\n".join([f"- {l.get('lesson_learned')}" for l in lessons]) if lessons else ""
    
    retrieved_memories = {
        "summary": summary,
        "entities": entities,
        "profile": profile,
        "budgets": budgets,
        "goals_db": goals_db,
        "subscriptions": subscriptions,
        "goals": goals,
        "preferences": preferences,
        "episodic": episodic,
        "timeline": timeline,
        "vector": vector_context
    }
    
    return {
        "retrieved_memories": retrieved_memories,
        "lessons_learned": lessons_str,
        "next_step": "supervisor"
    }


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "SupervisorNode"})
    query = state["user_query"]
    messages = state.get("messages", [])
    chat_context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-5:]])
    
    sup_res = await run_supervisor_agent(query, chat_context)
    
    return {
        "intent": sup_res["intent"],
        "risk_level": sup_res["risk_level"],
        "current_agent": sup_res["target_agent"],
        "next_step": "planner"
    }


async def planner_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "PlannerNode"})
    query = state["user_query"]
    intent = state["intent"]
    target_agent = state["current_agent"]
    
    retrieved = state.get("retrieved_memories") or {}
    summary = retrieved.get("summary", "")
    entities = retrieved.get("entities", {})
    goals = retrieved.get("goals", [])
    prefs = retrieved.get("preferences", {})
    lessons = state.get("lessons_learned", "")
    
    memory_context = (
        f"Summary: {summary}\n"
        f"Entities: {json.dumps(entities)}\n"
        f"Goals: {json.dumps(goals)}\n"
        f"Preferences: {json.dumps(prefs)}\n"
        f"Lessons: {lessons}"
    )
    
    plan_res = await run_planner_agent(query, intent, target_agent, memory_context)
    
    return {
        "execution_plan": plan_res["execution_plan"],
        "plan_steps": plan_res["plan_steps"],
        "current_step": 0,
        "next_step": "specialized_agent"
    }


async def specialized_agent_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "SpecializedAgentNode"})
    agent = state["current_agent"]
    query = state["user_query"]
    history = state.get("messages", [])
    retrieved = state.get("retrieved_memories") or {}
    
    memory_context = (
        f"Summary: {retrieved.get('summary', '')}\n"
        f"Entities: {json.dumps(retrieved.get('entities', {}))}\n"
        f"Goals: {json.dumps(retrieved.get('goals', []))}\n"
        f"Preferences: {json.dumps(retrieved.get('preferences', {}))}\n"
        f"Lessons: {state.get('lessons_learned', '')}"
    )
    
    compressed_history = await compress_context_tool(history)
    tools = []
    metrics = {}
    response = None
    
    # Route execution to correct specialist agent
    if agent == "financial_analysis_agent":
        res = await run_financial_analysis_agent(query, compressed_history)
        tools = res.get("tools", [])
        metrics = res.get("metrics", {})
    elif agent == "spending_analysis_agent":
        res = await run_spending_analysis_agent(query, compressed_history)
        tools = res.get("tools", [])
        metrics = res.get("metrics", {})
    elif agent == "pattern_detection_agent":
        res = await run_pattern_detection_agent(query, compressed_history)
        tools = res.get("tools", [])
        metrics = res.get("metrics", {})
    elif agent == "reporting_agent":
        res = await run_reporting_agent(query, compressed_history)
        tools = res.get("tools", [])
        metrics = res.get("metrics", {})
    elif agent == "email_agent":
        res = await run_email_agent(query, compressed_history, memory_context)
        tools = res.get("tools", [])
        metrics = res.get("metrics", {})
    elif agent == "recommendation_agent":
        res = await run_recommendation_agent(query, compressed_history, memory_context)
        response = res.get("response")
        tools = []
        metrics = res.get("metrics", {})
    elif agent == "memory_agent":
        res = await run_memory_agent(query, compressed_history)
        tools = res.get("tools", [])
        metrics = res.get("metrics", {})
    else:
        res = await run_recommendation_agent(query, compressed_history, memory_context)
        response = res.get("response")
        tools = []
        metrics = res.get("metrics", {})
        
    accumulate_metrics(metrics)
    
    state_updates = {
        "tools_to_call": tools,
    }
    if response:
        state_updates["response"] = response
        
    # Execute tools immediately inside the specialized agent execution loop
    tool_results = state.get("tool_results", {}).copy()
    if tools:
        async with SessionLocal() as db:
            for tool in tools:
                name = tool.get("name")
                args = tool.get("args", {})
                
                cached, cached_val = get_cached_tool_result(name, args)
                if cached:
                    log_trace("tool_cache_hit", {"tool": name})
                    tool_results[name] = cached_val
                    continue
                    
                log_trace("tool_call", {"tool": name, "args": args})
                outcome = {"status": "error", "data": {}, "metadata": {"error": "Tool not found"}}
                
                try:
                    # Retrieval Tools
                    if name == "aggregate_accounts_tool":
                        outcome = await aggregate_accounts_tool(db)
                    elif name == "retrieve_transactions_tool":
                        outcome = await retrieve_transactions_tool(db)
                    elif name == "retrieve_income_tool":
                        outcome = await retrieve_income_tool(db)
                    elif name == "retrieve_budgets_tool":
                        outcome = await retrieve_budgets_tool(db)
                    elif name == "retrieve_savings_goals_tool":
                        outcome = await retrieve_savings_goals_tool(db)
                    elif name == "retrieve_rag_knowledge_tool":
                        outcome = await retrieve_rag_knowledge_tool(args.get("query"), db)
                    
                    # Processing Tools
                    elif name == "process_bank_statement_text_tool":
                        outcome = await process_bank_statement_text_tool(args.get("raw_text"))
                    elif name == "process_pdf_statement_tool":
                        outcome = await process_pdf_statement_tool(args.get("file_path"))
                    
                    # Execution / Mutating Tools
                    elif name == "cancel_subscription_tool":
                        outcome = await cancel_subscription_tool(args.get("merchant"), db)
                    elif name == "update_budget_tool":
                        outcome = await update_budget_tool(args.get("category"), args.get("new_limit"), db)
                    elif name == "transfer_savings_tool":
                        outcome = await transfer_savings_tool(args.get("goal_name"), args.get("amount_to_transfer"), db)
                    elif name == "send_email_report_tool":
                        outcome = await send_email_report_tool(
                            recipient_email=args.get("recipient_email"),
                            subject=args.get("subject"),
                            body=args.get("body")
                        )
                    
                    # Analysis Tools
                    elif name == "analyze_spending_patterns_tool":
                        outcome = await analyze_spending_patterns_tool(db)
                    elif name == "forecast_month_end_tool":
                        outcome = await forecast_month_end_tool(db)
                    elif name == "detect_anomalies_tool":
                        outcome = await detect_anomalies_tool(db)
                        
                    # Verification Tools
                    elif name == "data_verification_tool":
                        outcome = await data_verification_tool(args.get("tool_output"), args.get("expected_schema"))
                    elif name == "financial_rules_verification_tool":
                        outcome = await financial_rules_verification_tool(args.get("amount"), args.get("date_str"))
                    elif name == "workflow_verification_tool":
                        outcome = await workflow_verification_tool(
                            args.get("original_intent"), args.get("plan_steps"), args.get("executed_steps")
                        )
                        
                    # Reporting Tools
                    elif name == "track_budget_variance_tool":
                        outcome = await track_budget_variance_tool(db)
                    elif name == "track_savings_goals_tool":
                        outcome = await track_savings_goals_tool(db)
                    elif name == "calculate_wellness_score_tool":
                        outcome = await calculate_wellness_score_tool(db)
                    elif name == "generate_financial_report_tool":
                        outcome = await generate_financial_report_tool(db)
                    elif name == "audit_report_tool":
                        outcome = await audit_report_tool(args.get("limit", 10), db)
                except Exception as e:
                    outcome = {"status": "error", "data": {}, "metadata": {"error": str(e)}}
                    
                set_cached_tool_result(name, args, outcome)
                tool_results[name] = outcome
                
    state_updates["tool_results"] = tool_results
    state_updates["next_step"] = "verification"
    return state_updates


def check_needs_approval(state: AgentState) -> bool:
    risk = state.get("risk_level", "low")
    tools = state.get("tools_to_call", [])
    
    mutating_tool_called = any(
        t.get("name") in [
            "cancel_subscription_tool",
            "update_budget_tool",
            "transfer_savings_tool"
        ] for t in tools
    )
    return (risk in ["high", "critical"]) or mutating_tool_called


async def verification_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "VerificationNode"})
    tool_results = state.get("tool_results", {})
    plan = state.get("execution_plan", "")
    
    # Layer 1 Tools Verification
    v1 = await verify_layer1_tools(tool_results)
    if v1.status == "FAILED":
        log_trace("verification_failed", {"layer": 1, "details": v1.details})
        return {
            "verification_status": "FAILED",
            "next_step": "retry"
        }
        
    # Layer 2 Agent Plan Verification
    v2 = await verify_layer2_agent(plan, tool_results, state.get("retrieved_memories"))
    if v2.status == "FAILED" or v2.status == "PARTIAL":
        log_trace("verification_failed", {"layer": 2, "details": v2.details})
        return {
            "verification_status": v2.status,
            "next_step": "retry"
        }
        
    needs_gate = check_needs_approval(state)
    if needs_gate:
        return {
            "verification_status": "PASSED",
            "approval_required": True,
            "next_step": "human_approval"
        }
    else:
        return {
            "verification_status": "PASSED",
            "approval_required": False,
            "next_step": "reflection"
        }


async def retry_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "RetryNode"})
    retries = state.get("retry_count", 0) + 1
    log_trace("workflow_retry", {"retry_count": retries})
    
    if retries > settings.MAX_RETRIES:
        log_trace("execution_failed", {"reason": "Max retries exceeded"})
        return {
            "response": "Workflow execution failed after maximum self-correction retries due to validation failures.",
            "next_step": "response"
        }
        
    return {
        "retry_count": retries,
        "tools_to_call": [],
        "next_step": "planner"
    }


async def human_approval_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "HumanApprovalNode"})
    app_granted = state.get("approval_granted", None)
    
    if app_granted is None:
        log_trace("human_approval_pause", {})
        return {
            "approval_required": True,
            "next_step": "human_approval"
        }
        
    if app_granted is False:
        log_trace("human_approval_rejected", {})
        return {
            "approval_required": False,
            "response": "Workflow execution rejected by human supervisor.",
            "next_step": "reflection"
        }
        
    log_trace("human_approval_granted", {})
    return {
        "approval_required": False,
        "next_step": "reflection"
    }


async def reflection_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "ReflectionNode"})
    user_id = state.get("user_id") or "user_1"
    verification_status = state.get("verification_status", "PASSED")
    approval_action = state.get("approval_action")
    query = state["user_query"]
    
    async with SessionLocal() as db:
        if verification_status == "FAILED":
            issue = f"Verification failed for query: '{query}'"
            lesson = "Ensure financial safety parameters are correctly input and values comply with ranges."
            await store_reflection(user_id, issue, lesson, db)
            log_trace("reflection_stored", {"issue": issue, "lesson": lesson})
        elif approval_action == "rejected" or state.get("approval_granted") is False:
            issue = f"User/Supervisor rejected the scheduled action for: '{query}'"
            lesson = "Confirm manual transfers or budget edits with the user before attempting execution node."
            await store_reflection(user_id, issue, lesson, db)
            log_trace("reflection_stored", {"issue": issue, "lesson": lesson})
            
        tool_results = state.get("tool_results", {})
        for tool_name, result in tool_results.items():
            if result.get("status") == "error":
                issue = f"Tool '{tool_name}' returned error: {result.get('metadata', {}).get('error')}"
                lesson = f"Check arguments passed to {tool_name} and ensure the target account or savings goal is active."
                await store_reflection(user_id, issue, lesson, db)
                log_trace("reflection_stored", {"issue": issue, "lesson": lesson})
                
    return {"next_step": "memory_update"}


async def memory_update_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "MemoryUpdateNode"})
    user_id = state.get("user_id") or "user_1"
    thread_id = state.get("thread_id") or "default_thread"
    query = state["user_query"]
    response = state.get("response", "")
    
    async with SessionLocal() as db:
        await check_and_trigger_summarization(user_id, thread_id, db)
        
        discovery_prompt = (
            "Analyze the user query and response to identify if any new permanent user financial goals, "
            "preferences, or personal entities (like name, preferred bank, etc.) were mentioned or established.\n"
            "Respond in JSON matching this schema:\n"
            "{\n"
            "  \"goal\": {\"goal_description\": \"...\", \"target_value\": 1000.0, \"target_date\": \"YYYY-MM-DD\"} or null,\n"
            "  \"preference\": {\"preference_type\": \"...\", \"preference_value\": \"...\"} or null,\n"
            "  \"entity\": {\"entity_name\": \"...\", \"entity_value\": \"...\"} or null\n"
            "}"
        )
        messages = [
            SystemMessage(content=discovery_prompt),
            HumanMessage(content=f"Query: {query}\nResponse: {response}")
        ]
        
        try:
            discovery_res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
            disc = json.loads(discovery_res["text"])
            
            if disc.get("goal"):
                g = disc["goal"]
                await save_goal(user_id, g["goal_description"], g["target_value"], g["target_date"], db=db)
            if disc.get("preference"):
                p = disc["preference"]
                await save_preference(user_id, p["preference_type"], p["preference_value"], db)
            if disc.get("entity"):
                e = disc["entity"]
                await save_user_entity(user_id, e["entity_name"], e["entity_value"], 1.0, db)
            await db.commit()
        except Exception as e:
            print(f"Error in memory discovery update: {e}")
            
    return {"next_step": "response"}


async def response_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "ResponseNode"})
    
    if state.get("response") and not state.get("tools_to_call"):
        final_text = state["response"]
    else:
        system_prompt = (
            "You are the Lead Financial Wellness Advisor. Based on the executed tool results, historical transactions, "
            "and budgeting analysis, formulate a professional, clear, complete, and action-oriented response to guide the user.\n"
            "Do not include raw code snippets or JSON structures in the response text. Present clean, markdown formatted information."
        )
        
        retrieved = state.get("retrieved_memories") or {}
        memory_context = f"Financial summary: {retrieved.get('summary', '')}\n"
        lessons = state.get("lessons_learned", "")
        lessons_context = f"\n### REFLECTION MEMORY (LESSONS LEARNED):\n{lessons}\n" if lessons else ""
     
        user_prompt = (
            f"Original query: {state['user_query']}\n\n"
            f"{memory_context}"
            f"{lessons_context}"
            f"Executed Tool outcomes: {json.dumps(state.get('tool_results', {}))}"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        res = await call_model(messages, settings.FAST_MODEL)
        accumulate_metrics(res)
        final_text = res["text"]
        
    # Layer 3 End-to-End verification
    v3 = await verify_layer3_e2e(state["user_query"], final_text)
    if v3.status == "FAILED":
        log_trace("verification_failed", {"layer": 3, "details": v3.details})
        final_text = f"Warning: Verification warning on this output.\n\n{final_text}"
        
    # Output Guardrail validation
    try:
        validate_output(final_text)
    except ValueError as e:
        error_msg = str(e)
        log_trace("output_guardrail_blocked", {"reason": error_msg})
        final_text = f"Security block: {error_msg}"
        
    log_trace("execution_success", {})
    return {
        "response": final_text,
        "messages": [AIMessage(content=final_text)],
        "next_step": "end"
    }


# --- Routing Logics ---

def route_from_start(state: AgentState) -> str:
    return "input_validation_node"

def route_from_input_validation(state: AgentState) -> str:
    if state.get("next_step") == "response":
        return "response_node"
    return "memory_retrieval_node"

def route_from_verification(state: AgentState) -> str:
    return state.get("next_step", "retry")

def route_from_retry(state: AgentState) -> str:
    if state.get("next_step") == "response":
        return "response_node"
    return "planner_node"

def route_from_human_approval(state: AgentState) -> str:
    if state.get("approval_required") and state.get("approval_granted") is None:
        return END
    return "reflection_node"


# --- Graph Assembly ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("input_validation_node", input_validation_node)
workflow.add_node("memory_retrieval_node", memory_retrieval_node)
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("planner_node", planner_node)
workflow.add_node("specialized_agent_node", specialized_agent_node)
workflow.add_node("verification_node", verification_node)
workflow.add_node("retry_node", retry_node)
workflow.add_node("human_approval_node", human_approval_node)
workflow.add_node("reflection_node", reflection_node)
workflow.add_node("memory_update_node", memory_update_node)
workflow.add_node("response_node", response_node)

# Add edges and conditional transitions
workflow.add_conditional_edges(START, route_from_start)

workflow.add_conditional_edges("input_validation_node", route_from_input_validation, {
    "response_node": "response_node",
    "memory_retrieval_node": "memory_retrieval_node"
})

workflow.add_edge("memory_retrieval_node", "supervisor_node")
workflow.add_edge("supervisor_node", "planner_node")
workflow.add_edge("planner_node", "specialized_agent_node")
workflow.add_edge("specialized_agent_node", "verification_node")

workflow.add_conditional_edges("verification_node", route_from_verification, {
    "retry": "retry_node",
    "human_approval": "human_approval_node",
    "reflection": "reflection_node"
})

workflow.add_conditional_edges("retry_node", route_from_retry, {
    "response_node": "response_node",
    "planner_node": "planner_node"
})

workflow.add_conditional_edges("human_approval_node", route_from_human_approval, {
    "reflection_node": "reflection_node",
    "__end__": END
})

workflow.add_edge("reflection_node", "memory_update_node")
workflow.add_edge("memory_update_node", "response_node")
workflow.add_edge("response_node", END)

# Compile graph with persistent AsyncSqliteSaver checkpointer and interrupt before approval node
_graph_app = None
_checkpointer = None

def get_graph_app():
    global _graph_app, _checkpointer
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None
    
    # Re-create if event loop changed (e.g. under pytest)
    if _graph_app is not None and _checkpointer is not None:
        if getattr(_checkpointer, "loop", None) is not loop:
            _graph_app = None
            _checkpointer = None
            
    if _graph_app is not None:
        return _graph_app
    
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    
    conn = aiosqlite.connect("finance_checkpoints.db")
    _checkpointer = AsyncSqliteSaver(conn)
    
    _graph_app = workflow.compile(
        checkpointer=_checkpointer,
        interrupt_before=["human_approval_node"]
    )
    return _graph_app


