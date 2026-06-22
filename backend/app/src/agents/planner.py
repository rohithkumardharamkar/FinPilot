import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings

async def run_planner_agent(
    user_query: str,
    intent: str,
    target_agent: str,
    memory_context: str
) -> Dict[str, Any]:
    """
    Planner Agent that understands objectives, references memory context,
    and breaks tasks down into actionable steps.
    """
    system_prompt = (
        "You are the Lead Personal Finance Planner Agent. Your job is to analyze the user's query, "
        "classified intent, target specialist agent, and the retrieved memory context, and generate a step-by-step execution plan "
        "to satisfy the user request.\n\n"
        "Retrieved Memory Context contains the user's goals, preferences, entities, summaries, episodic memories, and lessons learned. "
        "Use this context to customize the plan. For instance, if the user asks to email something, check memory context for their "
        "preferred email address.\n\n"
        "Your output must be strictly in JSON matching this schema:\n"
        "{\n"
        "  \"execution_plan\": \"A detailed text description of what needs to be done and why\",\n"
        "  \"plan_steps\": [\n"
        "    \"Step 1: description\",\n"
        "    \"Step 2: description\",\n"
        "    ...\n"
        "  ]\n"
        "}"
    )
    
    user_message_content = (
        f"User Query: {user_query}\n"
        f"Intent: {intent}\n"
        f"Target Agent: {target_agent}\n\n"
        f"Retrieved Memory Context:\n{memory_context}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message_content)
    ]
    
    res = await call_model(messages, settings.REASONING_MODEL, json_mode=True)
    
    try:
        parsed = json.loads(res["text"])
        return {
            "execution_plan": parsed.get("execution_plan", "Run specialist tools to resolve the query."),
            "plan_steps": parsed.get("plan_steps", ["1. Execute target agent tasks", "2. Respond to user"]),
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
    except Exception:
        # Fallback plan generation
        plan_steps = [f"1. Query relevant tools for {intent}"]
        if intent == "email_request":
            plan_steps.append("2. Extract recipient email and draft report")
            plan_steps.append("3. Call email sending tool")
        elif "cancel" in user_query.lower() or "update" in user_query.lower() or "transfer" in user_query.lower():
            plan_steps.append("2. Request user approval for mutating action")
            plan_steps.append("3. Execute mutating operation")
        else:
            plan_steps.append("2. Analyze results and generate wellness advice")
        plan_steps.append("4. Return final response to user")
        
        return {
            "execution_plan": f"Execute fallback plan for intent {intent}.",
            "plan_steps": plan_steps,
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
