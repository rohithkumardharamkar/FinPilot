import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings

async def run_supervisor_agent(user_query: str, chat_context: str = "") -> Dict[str, Any]:
    """
    Supervisor Agent executing Intent Detection, Risk Assessment, and Priority Detection.
    Classifies the user query and routes to the appropriate specialist agent.
    """
    system_prompt = (
        "You are the Lead Personal Finance Supervisor. Your task is to analyze the user's "
        "financial query, classify the intent, detect the priority, assess the risk level, and output routing parameters.\n\n"
        "Do NOT answer the query directly. Only output the classification in JSON.\n\n"
        "Intents to choose from:\n"
        "- greeting: Hello, hi, etc.\n"
        "- general_chat: non-financial chit chat\n"
        "- financial_analysis: queries about accounts, balances, net worth\n"
        "- spending_analysis: queries about transactions, transaction history\n"
        "- pattern_analysis: queries about trends, anomalies, forecasting\n"
        "- report_generation: requests to generate report or summary of financial wellness\n"
        "- recommendation_request: requests for financial advice/wellness recommendations\n"
        "- memory_recall: asking to recall something previously said or remembered\n"
        "- goal_management: adding, updating, tracking, or deleting savings goals\n"
        "- email_request: asking to email a report, balance, statement, etc.\n"
        "- dashboard_query: asking for dashboard summary or stats\n"
        "- follow_up_question: a follow-up query relying on previous chat context\n"
        "- clarification_request: asking for explanation of previous answer\n"
        "- unknown: anything else\n\n"
        "Priority to choose from:\n"
        "- high: urgent financial requests, errors, or critical alerts\n"
        "- medium: standard reports, goals, budget modifications\n"
        "- low: greetings, general chat, casual questions\n\n"
        "Risk levels to choose from:\n"
        "- low: read-only lookups, greetings, general chat, memory recall\n"
        "- medium: standard calculations, pattern reports, report generation, email requests\n"
        "- high: modifying budget limits or transferring money (mutating operations), goal management\n"
        "- critical: cancelling subscriptions (mutating operations)\n\n"
        "You MUST output a JSON response matching this exact schema:\n"
        "{\n"
        "  \"intent\": \"greeting|general_chat|financial_analysis|spending_analysis|pattern_analysis|report_generation|recommendation_request|memory_recall|goal_management|email_request|dashboard_query|follow_up_question|clarification_request|unknown\",\n"
        "  \"priority\": \"low|medium|high\",\n"
        "  \"risk_level\": \"low|medium|high|critical\",\n"
        "  \"target_agent\": \"financial_analysis_agent|spending_analysis_agent|pattern_detection_agent|reporting_agent|email_agent|recommendation_agent|memory_agent\",\n"
        "  \"reasoning\": \"Brief explanation of your classification\"\n"
        "}"
    )
    
    query_text = f"User Query: {user_query}"
    if chat_context:
        query_text = f"Chat Context:\n{chat_context}\n\n{query_text}"
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query_text)
    ]
    
    res = await call_model(messages, settings.REASONING_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "intent": parsed.get("intent", "financial_analysis"),
            "priority": parsed.get("priority", "medium"),
            "risk_level": parsed.get("risk_level", "low"),
            "target_agent": parsed.get("target_agent", "financial_analysis_agent"),
            "reasoning": parsed.get("reasoning", ""),
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
    except Exception:
        # Fallback python classification
        intent = "financial_analysis"
        target_agent = "financial_analysis_agent"
        priority = "medium"
        risk_level = "low"
        
        query_lower = user_query.lower()
        if "hello" in query_lower or "hi" in query_lower or "hey" in query_lower:
            intent = "greeting"
            target_agent = "recommendation_agent"
            priority = "low"
        elif "email" in query_lower or "send to" in query_lower:
            intent = "email_request"
            target_agent = "email_agent"
            priority = "medium"
            risk_level = "medium"
        elif "report" in query_lower or "summary" in query_lower:
            intent = "report_generation"
            target_agent = "reporting_agent"
            priority = "medium"
            risk_level = "medium"
        elif "pattern" in query_lower or "spend" in query_lower or "trend" in query_lower or "forecast" in query_lower:
            intent = "pattern_analysis"
            target_agent = "pattern_detection_agent"
            priority = "medium"
            risk_level = "low"
        elif "cancel" in query_lower:
            intent = "goal_management"
            target_agent = "memory_agent"
            priority = "high"
            risk_level = "critical"
        elif "budget" in query_lower or "goal" in query_lower or "save" in query_lower:
            intent = "goal_management"
            target_agent = "memory_agent"
            priority = "medium"
            risk_level = "high"
            
        return {
            "intent": intent,
            "priority": priority,
            "risk_level": risk_level,
            "target_agent": target_agent,
            "reasoning": "Fallback parsing due to non-JSON output",
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }

