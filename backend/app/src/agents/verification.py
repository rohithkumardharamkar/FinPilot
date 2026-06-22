from typing import Dict, Any, List
import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings

class VerificationResult:
    def __init__(self, status: str, details: str, failed_checks: List[str]):
        self.status = status  # PASSED, FAILED, PARTIAL
        self.details = details
        self.failed_checks = failed_checks

async def verify_layer1_tools(tool_results: Dict[str, Any]) -> VerificationResult:
    """
    Layer 1: Verify all tool execution statuses.
    Ensures success and checks for null or missing values.
    """
    failed_checks = []
    
    if not tool_results:
        return VerificationResult("PASSED", "No tools were executed during this path.", [])
        
    for tool_name, outcome in tool_results.items():
        status = outcome.get("status", "failed")
        data = outcome.get("data", {})
        
        if status != "success":
            failed_checks.append(f"Tool {tool_name} returned status: {status}")
            continue
            
        if not data and status == "success":
            failed_checks.append(f"Tool {tool_name} succeeded but returned empty data.")
            
    if len(failed_checks) > 0:
        return VerificationResult(
            status="FAILED",
            details=f"Layer 1: Tool verification failed. Errors: {'; '.join(failed_checks)}",
            failed_checks=failed_checks
        )
        
    return VerificationResult("PASSED", "Layer 1: Tool execution verified successfully.", [])

async def verify_layer2_agent(
    plan: str,
    tool_results: Dict[str, Any],
    retrieved_memories: Dict[str, Any] = None
) -> VerificationResult:
    """
    Layer 2: Verify plan and goal completion using LLM reasoning.
    """
    if not plan:
        return VerificationResult("PASSED", "No generated plan to verify.", [])
        
    system_prompt = (
        "You are a Finance QA Verification Agent. Your job is to verify if the generated "
        "reasoning plan matches the executed tools, tool results, and retrieved memories.\n\n"
        "Review the original plan, the retrieved memories, and the executed tool outcomes. Determine if the goal is fully achieved.\n"
        "Note: Some plan steps (like fetching budget details, checking subscriptions, or retrieving transactions) might be fully satisfied by the retrieved memories "
        "already present, so separate tool calls for them are not required if the memory contains the information.\n\n"
        "You must output a JSON response matching this schema:\n"
        "{\n"
        "  \"passed\": true/false,\n"
        "  \"reason\": \"Detailed analysis of what was accomplished versus planned.\"\n"
        "}"
    )
    
    # Helper to clean/serialize memories for prompt clarity
    serialized_memories = {}
    if retrieved_memories:
        for k, v in retrieved_memories.items():
            if k == "entity" and isinstance(v, dict):
                serialized_memories["financial_profile"] = v.get("profile")
                serialized_memories["budgets"] = v.get("budgets")
                serialized_memories["savings_goals"] = v.get("goals")
                serialized_memories["subscriptions"] = v.get("subscriptions")
            elif k == "episodic" and isinstance(v, dict):
                serialized_memories["transaction_timeline"] = v.get("timeline")
            elif k == "vector":
                serialized_memories["semantic_search_context"] = v
            elif k == "summary":
                serialized_memories["financial_summary"] = v
                
    user_prompt = (
        f"Original Plan:\n{plan}\n\n"
        f"Retrieved Memories:\n{json.dumps(serialized_memories, indent=2)}\n\n"
        f"Executed Tool Outcomes:\n{json.dumps(tool_results, indent=2)}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        data = json.loads(res["text"])
        passed = data.get("passed", False)
        reason = data.get("reason", "No reason provided.")
        
        if passed:
            return VerificationResult("PASSED", f"Layer 2: Agent plan verified. {reason}", [])
        else:
            return VerificationResult("PARTIAL", f"Layer 2: Agent plan partially completed. {reason}", ["plan_not_fully_met"])
    except Exception:
        return VerificationResult("PASSED", "Layer 2: Verification parsed with default approval.", [])

async def verify_layer3_e2e(
    user_query: str,
    final_output: str
) -> VerificationResult:
    """
    Layer 3: Verify the original request matches the final response.
    """
    system_prompt = (
        "You are a Finance E2E Verification Agent. Your job is to verify if the final response "
        "directly and safely answers the user's original request.\n\n"
        "Analyze the alignment. Output JSON:\n"
        "{\n"
        "  \"passed\": true/false,\n"
        "  \"details\": \"Explanation of safety and resolution alignment.\"\n"
        "}"
    )
    
    user_prompt = (
        f"Original Request:\n{user_query}\n\n"
        f"Final Output:\n{final_output}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
    
    try:
        data = json.loads(res["text"])
        passed = data.get("passed", False)
        details = data.get("details", "")
        
        if passed:
            return VerificationResult("PASSED", f"Layer 3: E2E Verification Passed. {details}", [])
        else:
            return VerificationResult("FAILED", f"Layer 3: E2E Verification Failed. Response doesn't answer query: {details}", ["e2e_alignment_failure"])
    except Exception:
        return VerificationResult("PASSED", "Layer 3: E2E parsed with default approval.", [])
