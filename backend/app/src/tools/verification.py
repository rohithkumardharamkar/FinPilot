import re
from typing import Dict, Any, List

async def data_verification_tool(tool_output: Dict[str, Any], expected_schema: List[str]) -> Dict[str, Any]:
    """
    Validates tool execution schema, success flag, and checks for any null/empty fields
    in key paths (Layer 1).
    """
    try:
        status = tool_output.get("status", "failed")
        data = tool_output.get("data", {})
        
        if status not in ["success", "completed"]:
            return {
                "status": "failed",
                "data": {"passed": False, "reason": f"Tool output indicates status: {status}"},
                "metadata": {}
            }
            
        missing_keys = []
        null_keys = []
        
        for key in expected_schema:
            if key not in data:
                missing_keys.append(key)
            elif data[key] is None or data[key] == "":
                null_keys.append(key)
                
        passed = len(missing_keys) == 0 and len(null_keys) == 0
        reason = "All schema elements validated successfully."
        if not passed:
            reason = f"Schema validation failed. Missing: {missing_keys}, Null/Empty: {null_keys}"
            
        return {
            "status": "success",
            "data": {
                "passed": passed,
                "reason": reason,
                "missing_keys": missing_keys,
                "null_keys": null_keys
            },
            "metadata": {"verifier": "layer1_data_verification"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {"passed": False, "reason": str(e)},
            "metadata": {}
        }

async def financial_rules_verification_tool(
    amount: float,
    date_str: str = None
) -> Dict[str, Any]:
    """Verifies spending, budget, or transaction constraints (amounts, date formats)."""
    try:
        passed = True
        reason = "Financial transaction details verified successfully."
        
        if amount <= 0:
            passed = False
            reason = f"Invalid amount: ₹{amount}. Amount must be greater than zero."
            
        if date_str:
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            if not date_pattern.match(date_str):
                passed = False
                reason = f"Invalid date format: {date_str}. Expected YYYY-MM-DD."
                
        return {
            "status": "success",
            "data": {
                "passed": passed,
                "reason": reason
            },
            "metadata": {"verifier": "financial_rules_verification"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {"passed": False, "reason": str(e)},
            "metadata": {}
        }

async def workflow_verification_tool(
    original_intent: str,
    plan_steps: List[str],
    executed_steps: List[str]
) -> Dict[str, Any]:
    """Validates that all steps generated in the planning phase were successfully navigated (Layer 2)."""
    try:
        missing_steps = [step for step in plan_steps if step not in executed_steps]
        passed = len(missing_steps) == 0
        
        reason = "Workflow path corresponds to the generated plan."
        if not passed:
            reason = f"Workflow incomplete. Missing planned steps: {missing_steps}"
            
        return {
            "status": "success",
            "data": {
                "passed": passed,
                "reason": reason,
                "missing_steps": missing_steps
            },
            "metadata": {"verifier": "layer2_workflow_verification"}
        }
    except Exception as e:
        return {
            "status": "error",
            "data": {"passed": False, "reason": str(e)},
            "metadata": {}
        }
