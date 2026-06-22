import time
from typing import Dict, Any, List
from src.core.config import settings

# Global session metrics telemetry
_TELEMETRY = {
    "total_queries": 0,
    "selected_models": {},
    "agent_paths": [],
    "total_tool_calls": 0,
    "total_retries": 0,
    "total_failures": 0,
    "guardrail_events": 0,
    "human_approvals": 0,
    
    # Cumulative stats
    "cumulative_input_tokens": 0,
    "cumulative_output_tokens": 0,
    "cumulative_cost": 0.0,
    "cumulative_latency": 0.0,
    "successful_runs": 0,
    "verified_passed_runs": 0
}

def log_trace(event_type: str, details: Dict[str, Any]):
    """Log trace logs to shell and accumulate analytics."""
    global _TELEMETRY
    print(f"[TRACE] {event_type} - {details}")
    
    if event_type == "query_received":
        _TELEMETRY["total_queries"] += 1
    elif event_type == "model_selected":
        m = details.get("model", "unknown")
        _TELEMETRY["selected_models"][m] = _TELEMETRY["selected_models"].get(m, 0) + 1
    elif event_type == "agent_transition":
        path = details.get("agent", "unknown")
        _TELEMETRY["agent_paths"].append(path)
    elif event_type == "tool_call":
        _TELEMETRY["total_tool_calls"] += 1
    elif event_type == "workflow_retry":
        _TELEMETRY["total_retries"] += 1
    elif event_type == "guardrail_violation":
        _TELEMETRY["guardrail_events"] += 1
    elif event_type == "human_approval_pause":
        _TELEMETRY["human_approvals"] += 1
    elif event_type == "execution_failed":
        _TELEMETRY["total_failures"] += 1
    elif event_type == "execution_success":
        _TELEMETRY["successful_runs"] += 1
        if details.get("verification_status") == "PASSED":
            _TELEMETRY["verified_passed_runs"] += 1

def accumulate_metrics(metrics: Dict[str, Any]):
    """Accumulate token counts, latencies, and cost estimations."""
    global _TELEMETRY
    _TELEMETRY["cumulative_input_tokens"] += metrics.get("input_tokens", 0)
    _TELEMETRY["cumulative_output_tokens"] += metrics.get("output_tokens", 0)
    _TELEMETRY["cumulative_cost"] += metrics.get("cost", 0.0)
    _TELEMETRY["cumulative_latency"] += metrics.get("latency", 0.0)

def get_observability_metrics() -> Dict[str, Any]:
    """Calculates all key rates required for production dashboards."""
    global _TELEMETRY
    total = _TELEMETRY["total_queries"] or 1
    
    success_rate = (_TELEMETRY["successful_runs"] / total) * 100
    verification_rate = (_TELEMETRY["verified_passed_runs"] / total) * 100
    retry_rate = (_TELEMETRY["total_retries"] / total) * 100
    guardrail_block_rate = (_TELEMETRY["guardrail_events"] / total) * 100
    
    avg_latency = (_TELEMETRY["cumulative_latency"] / total) if _TELEMETRY["cumulative_latency"] > 0 else 0.0
    
    return {
        "user_queries_processed": _TELEMETRY["total_queries"],
        "model_distribution": _TELEMETRY["selected_models"],
        "agent_paths_recorded": _TELEMETRY["agent_paths"],
        "tool_calls_executed": _TELEMETRY["total_tool_calls"],
        "retries_count": _TELEMETRY["total_retries"],
        "failures_count": _TELEMETRY["total_failures"],
        "guardrail_events_triggered": _TELEMETRY["guardrail_events"],
        "human_approvals_requested": _TELEMETRY["human_approvals"],
        "total_tokens_consumed": _TELEMETRY["cumulative_input_tokens"] + _TELEMETRY["cumulative_output_tokens"],
        "total_cost_usd": round(_TELEMETRY["cumulative_cost"], 6),
        
        # Computed Rates
        "success_rate_percentage": round(success_rate, 2),
        "verification_rate_percentage": round(verification_rate, 2),
        "retry_rate_percentage": round(retry_rate, 2),
        "guardrail_block_rate_percentage": round(guardrail_block_rate, 2),
        "average_latency_seconds": round(avg_latency, 3)
    }
