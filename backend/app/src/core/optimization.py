from typing import List, Dict, Any, Tuple, Optional
import json
import hashlib
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from src.agents.router import _TOOL_CACHE, estimate_tokens
from src.core.config import settings

# Trackers for Optimization metrics
_OPTIMIZATION_METRICS = {
    "tokens_saved": 0,
    "cache_hits": 0,
    "context_reduction_percentage": 0.0,
    "total_reductions": 0
}

def get_optimization_metrics() -> Dict[str, Any]:
    """Retrieve optimization statistics."""
    global _OPTIMIZATION_METRICS
    return _OPTIMIZATION_METRICS.copy()

def update_cache_metrics(tokens: int):
    """Log a response cache hit and tokens saved."""
    global _OPTIMIZATION_METRICS
    _OPTIMIZATION_METRICS["cache_hits"] += 1
    _OPTIMIZATION_METRICS["tokens_saved"] += tokens

async def compress_context_tool(messages: List[BaseMessage], max_tokens: int = 1500) -> List[BaseMessage]:
    """
    Compresses conversation context. If the estimated tokens of all messages exceed max_tokens,
    summarizes messages older than the last 4 messages and replaces them with a summary system message.
    """
    global _OPTIMIZATION_METRICS
    
    total_tokens = sum(estimate_tokens(m.content) for m in messages)
    if total_tokens <= max_tokens:
        return messages
        
    # We need to compress
    if len(messages) <= 5:
        # Too few messages, just return
        return messages
        
    # Keep System prompt (usually at index 0) and the last 4 messages
    sys_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    non_sys = [m for m in messages if not isinstance(m, SystemMessage)]
    
    if len(non_sys) <= 4:
        return messages
        
    to_summarize = non_sys[:-4]
    to_keep = non_sys[-4:]
    
    # Simple offline summarization simulation to save tokens
    summary_text = "Summary of previous discussion: "
    topics = []
    for msg in to_summarize:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        content = msg.content.lower()
        if "symptom" in content or "fever" in content:
            topics.append("symptom logging")
        elif "appointment" in content or "schedule" in content:
            topics.append("appointment scheduling")
        elif "patient" in content or "profile" in content:
            topics.append("patient profile verification")
            
    if topics:
        summary_text += f"Discussed {', '.join(set(topics))}."
    else:
        summary_text += "Exchanged medical details."
        
    summary_msg = SystemMessage(content=summary_text)
    
    # Reconstruct messages list
    new_messages = []
    if sys_msgs:
        new_messages.append(sys_msgs[0])
    new_messages.append(summary_msg)
    new_messages.extend(to_keep)
    
    new_tokens = sum(estimate_tokens(m.content) for m in new_messages)
    saved = total_tokens - new_tokens
    
    # Update stats
    _OPTIMIZATION_METRICS["tokens_saved"] += saved
    _OPTIMIZATION_METRICS["total_reductions"] += 1
    pct = (saved / total_tokens) * 100
    _OPTIMIZATION_METRICS["context_reduction_percentage"] = (
        (_OPTIMIZATION_METRICS["context_reduction_percentage"] * (_OPTIMIZATION_METRICS["total_reductions"] - 1) + pct)
        / _OPTIMIZATION_METRICS["total_reductions"]
    )
    
    return new_messages

def get_cached_tool_result(tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Retrieve cached tool result if exists."""
    global _OPTIMIZATION_METRICS
    arg_hash = hashlib.sha256(json.dumps(args, sort_keys=True).encode("utf-8")).hexdigest()
    cache_key = f"{tool_name}:{arg_hash}"
    
    if cache_key in _TOOL_CACHE:
        _OPTIMIZATION_METRICS["cache_hits"] += 1
        # Estimate tokens saved (approx 150 tokens per tool outcome)
        _OPTIMIZATION_METRICS["tokens_saved"] += 150
        return True, _TOOL_CACHE[cache_key].copy()
    return False, None

def set_cached_tool_result(tool_name: str, args: Dict[str, Any], result: Dict[str, Any]):
    """Save tool result to cache."""
    arg_hash = hashlib.sha256(json.dumps(args, sort_keys=True).encode("utf-8")).hexdigest()
    cache_key = f"{tool_name}:{arg_hash}"
    _TOOL_CACHE[cache_key] = result

def clear_caches():
    """Clear response and tool caches."""
    global _OPTIMIZATION_METRICS
    from src.agents.router import _RESPONSE_CACHE, _TOOL_CACHE
    _RESPONSE_CACHE.clear()
    _TOOL_CACHE.clear()
    _OPTIMIZATION_METRICS.update({
        "tokens_saved": 0,
        "cache_hits": 0,
        "context_reduction_percentage": 0.0,
        "total_reductions": 0
    })
