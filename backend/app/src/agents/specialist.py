import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings

async def run_financial_analysis_agent(user_query: str, chat_history: List[Any]) -> Dict[str, Any]:
    """
    Financial Analysis Agent: Manages accounts and income retrieval.
    """
    system_prompt = (
        "You are the Financial Analysis Specialist Agent. Your job is to select the appropriate "
        "retrieved account or income tool based on the user request. Respond with a JSON object.\n\n"
        "Available tools:\n"
        "1. aggregate_accounts_tool (params: none)\n"
        "2. retrieve_income_tool (params: none)\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  \"reasoning\": \"Why this tool is selected.\",\n"
        "  \"tool_name\": \"aggregate_accounts_tool|retrieve_income_tool\",\n"
        "  \"tool_params\": {}\n"
        "}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_query)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "reasoning": parsed.get("reasoning", ""),
            "tools": [{"name": parsed.get("tool_name"), "args": parsed.get("tool_params", {})}],
            "metrics": res
        }
    except Exception:
        tool_name = "aggregate_accounts_tool"
        if "income" in user_query.lower() or "salary" in user_query.lower():
            tool_name = "retrieve_income_tool"
            
        return {
            "reasoning": "Fallback routing based on query matching.",
            "tools": [{"name": tool_name, "args": {}}],
            "metrics": res
        }

async def run_spending_analysis_agent(user_query: str, chat_history: List[Any]) -> Dict[str, Any]:
    """
    Spending Analysis Agent: Manages transaction list queries.
    """
    system_prompt = (
        "You are the Spending Analysis Specialist Agent. Your job is to select the appropriate "
        "transaction retrieval tool based on the user request. Respond with a JSON object.\n\n"
        "Available tools:\n"
        "1. retrieve_transactions_tool (params: none)\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  \"reasoning\": \"Why this tool is selected.\",\n"
        "  \"tool_name\": \"retrieve_transactions_tool\",\n"
        "  \"tool_params\": {}\n"
        "}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_query)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "reasoning": parsed.get("reasoning", ""),
            "tools": [{"name": parsed.get("tool_name"), "args": parsed.get("tool_params", {})}],
            "metrics": res
        }
    except Exception:
        return {
            "reasoning": "Fallback routing to retrieve_transactions_tool.",
            "tools": [{"name": "retrieve_transactions_tool", "args": {}}],
            "metrics": res
        }

async def run_pattern_detection_agent(user_query: str, chat_history: List[Any]) -> Dict[str, Any]:
    """
    Pattern Detection Agent: Identifies spending patterns, trends, forecasters, and anomalies.
    """
    system_prompt = (
        "You are the Pattern Detection Specialist Agent. Your job is to select the appropriate "
        "pattern analysis, month-end forecaster, or anomaly/fraud detection tool. Respond with a JSON object.\n\n"
        "Available tools:\n"
        "1. analyze_spending_patterns_tool (params: none)\n"
        "2. forecast_month_end_tool (params: none)\n"
        "3. detect_anomalies_tool (params: none)\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  \"reasoning\": \"Why this tool is selected.\",\n"
        "  \"tool_name\": \"analyze_spending_patterns_tool|forecast_month_end_tool|detect_anomalies_tool\",\n"
        "  \"tool_params\": {}\n"
        "}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_query)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "reasoning": parsed.get("reasoning", ""),
            "tools": [{"name": parsed.get("tool_name"), "args": parsed.get("tool_params", {})}],
            "metrics": res
        }
    except Exception:
        tool_name = "analyze_spending_patterns_tool"
        if "forecast" in user_query.lower() or "burn" in user_query.lower() or "month-end" in user_query.lower():
            tool_name = "forecast_month_end_tool"
        elif "fraud" in user_query.lower() or "anomaly" in user_query.lower() or "suspicious" in user_query.lower():
            tool_name = "detect_anomalies_tool"
            
        return {
            "reasoning": "Fallback parsing spending tools from query.",
            "tools": [{"name": tool_name, "args": {}}],
            "metrics": res
        }

async def run_reporting_agent(user_query: str, chat_history: List[Any]) -> Dict[str, Any]:
    """
    Reporting Agent: Compiles budget variances, savings goals progress, and wellness scoring.
    """
    system_prompt = (
        "You are the Reporting Specialist Agent. Your job is to select the correct budget tracking, "
        "savings goal, wellness scoring, or financial health report tool. Respond with a JSON object.\n\n"
        "Available tools:\n"
        "1. track_budget_variance_tool (params: none)\n"
        "2. track_savings_goals_tool (params: none)\n"
        "3. calculate_wellness_score_tool (params: none)\n"
        "4. generate_financial_report_tool (params: none)\n"
        "5. audit_report_tool (params: limit: int)\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  \"reasoning\": \"Reporting tool selection rationale.\",\n"
        "  \"tool_name\": \"track_budget_variance_tool|track_savings_goals_tool|calculate_wellness_score_tool|generate_financial_report_tool|audit_report_tool\",\n"
        "  \"tool_params\": {}\n"
        "}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_query)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "reasoning": parsed.get("reasoning", ""),
            "tools": [{"name": parsed.get("tool_name"), "args": parsed.get("tool_params", {})}],
            "metrics": res
        }
    except Exception:
        tool_name = "generate_financial_report_tool"
        params = {}
        if "audit" in user_query.lower() or "log" in user_query.lower():
            tool_name = "audit_report_tool"
            params = {"limit": 10}
        elif "budget" in user_query.lower():
            tool_name = "track_budget_variance_tool"
        elif "goal" in user_query.lower() or "saving" in user_query.lower():
            tool_name = "track_savings_goals_tool"
        elif "score" in user_query.lower() or "wellness" in user_query.lower():
            tool_name = "calculate_wellness_score_tool"
            
        return {
            "reasoning": "Fallback routing report tool",
            "tools": [{"name": tool_name, "args": params}],
            "metrics": res
        }

async def run_email_agent(
    user_query: str,
    chat_history: List[Any],
    memory_context: str = ""
) -> Dict[str, Any]:
    """
    Email Agent: Extract recipient email, subject, and report, then execute send_email_report_tool.
    """
    system_prompt = (
        "You are the Email Specialist Agent. Your job is to extract the recipient email address, "
        "a suitable subject, and draft a clean, professional financial message based on the user's request and memory context.\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  \"reasoning\": \"Email details extraction explanation.\",\n"
        "  \"recipient_email\": \"user@example.com\",\n"
        "  \"subject\": \"Subject of the email\",\n"
        "  \"body\": \"Full formatted text/body of the email.\"\n"
        "}"
    )
    
    user_content = (
        f"User Query: {user_query}\n\n"
        f"Memory Context:\n{memory_context}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_content)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        recipient = parsed.get("recipient_email") or "user@example.com"
        subject = parsed.get("subject") or "Personal Financial Report Update"
        body = parsed.get("body") or "Please find attached your updated financial report details."
        
        return {
            "reasoning": parsed.get("reasoning", "Extracted email parameters from query."),
            "tools": [{
                "name": "send_email_report_tool",
                "args": {
                    "recipient_email": recipient,
                    "subject": subject,
                    "body": body
                }
            }],
            "metrics": res
        }
    except Exception:
        # Fallback parameters
        recipient = "user@example.com"
        if "user@example.com" not in user_query and "@" in user_query:
            # Simple extraction check
            for word in user_query.split():
                if "@" in word:
                    recipient = word.strip(".,!?;:")
                    break
        
        return {
            "reasoning": "Fallback routing to send_email_report_tool.",
            "tools": [{
                "name": "send_email_report_tool",
                "args": {
                    "recipient_email": recipient,
                    "subject": "Personal Financial Report Update",
                    "body": "Here is the summary of your account balance, transaction status, and financial wellness suggestions."
                }
            }],
            "metrics": res
        }

async def run_recommendation_agent(user_query: str, chat_history: List[Any], memory_context: str = "") -> Dict[str, Any]:
    """
    Recommendation Agent: Formulates final text responses, general chitchat, and advice directly.
    """
    system_prompt = (
        "You are the Financial Recommendation and Advisor Agent. Your task is to analyze the user query, "
        "conversation context, and retrieved memories to formulate a comprehensive, tailored response or advice.\n"
        "Provide professional, empathetic, and clear guidance on budgets, savings goals, or general financial topics.\n"
    )
    
    user_content = (
        f"User Query: {user_query}\n\n"
        f"Retrieved Memories:\n{memory_context}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_content)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=False)
    
    return {
        "reasoning": "Direct advice generated via LLM reasoning.",
        "response": res["text"],
        "tools": [],
        "metrics": res
    }

async def run_memory_agent(user_query: str, chat_history: List[Any]) -> Dict[str, Any]:
    """
    Memory & Action Specialist Agent: Mutates DB state for budgets, subscriptions, or savings.
    """
    system_prompt = (
        "You are the Memory & Actions Specialist Agent. Your job is to select the correct mutating tool "
        "to apply user updates or cancellations to budgets, subscriptions, or savings goals.\n\n"
        "Available tools:\n"
        "1. update_budget_tool (params: category: str, new_limit: float)\n"
        "2. transfer_savings_tool (params: goal_name: str, amount_to_transfer: float)\n"
        "3. cancel_subscription_tool (params: merchant: str)\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  \"reasoning\": \"Mutating tool selection explanation.\",\n"
        "  \"tool_name\": \"update_budget_tool|transfer_savings_tool|cancel_subscription_tool\",\n"
        "  \"tool_params\": {}\n"
        "}"
    )
    
    messages = [SystemMessage(content=system_prompt)] + chat_history + [HumanMessage(content=user_query)]
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "reasoning": parsed.get("reasoning", ""),
            "tools": [{"name": parsed.get("tool_name"), "args": parsed.get("tool_params", {})}],
            "metrics": res
        }
    except Exception:
        tool_name = "update_budget_tool"
        params = {}
        query_lower = user_query.lower()
        if "cancel" in query_lower:
            tool_name = "cancel_subscription_tool"
            merchant = "spotify"
            for m in ["netflix", "spotify", "chatgpt"]:
                if m in query_lower:
                    merchant = m
            params = {"merchant": merchant}
        elif "transfer" in query_lower or "save" in query_lower:
            tool_name = "transfer_savings_tool"
            params = {"goal_name": "Europe Trip", "amount_to_transfer": 5000.0}
        else:
            params = {"category": "Food", "new_limit": 5000.0}
            
        return {
            "reasoning": "Fallback parsing mutating tool parameters.",
            "tools": [{"name": tool_name, "args": params}],
            "metrics": res
        }
