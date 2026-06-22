import os
import csv
import time
import json
import hmac
import hashlib
import base64
from typing import Optional
from datetime import datetime

SECRET_KEY = "finpilot_secret_key"

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify SHA-256 password hash."""
    return hash_password(password) == hashed

def create_access_token(data: dict, expires_in: int = 86400) -> str:
    """Generate simple signed JWT token."""
    payload = data.copy()
    payload["exp"] = time.time() + expires_in
    
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify signed JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        
        # Check signature match
        if sig_b64 != expected_sig_b64:
            return None
            
        payload_dec = base64.urlsafe_b64decode(payload_b64 + "=" * (4 - len(payload_b64) % 4))
        payload = json.loads(payload_dec.decode())
        
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None


# --- CSV Logging Helpers ---

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")

def append_to_csv(filename: str, headers: list[str], row: dict):
    """Safely append a row to a CSV file in the csv/ directory."""
    os.makedirs(CSV_DIR, exist_ok=True)
    filepath = os.path.join(CSV_DIR, filename)
    file_exists = os.path.exists(filepath)
    
    # We append using mode 'a'
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def log_conversation_csv(user_id: str, thread_id: str, user_message: str, assistant_response: str):
    headers = ["timestamp", "user_id", "thread_id", "user_message", "assistant_response"]
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "thread_id": thread_id,
        "user_message": user_message,
        "assistant_response": assistant_response
    }
    append_to_csv("conversation_report.csv", headers, row)

def log_agent_action_csv(action: str, agent: str, status: str, details: str):
    headers = ["timestamp", "action", "agent", "status", "details"]
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "agent": agent,
        "status": status,
        "details": details
    }
    append_to_csv("agent_logs.csv", headers, row)
    append_to_csv("audit_logs.csv", headers, row)

def log_usage_stats_csv(user_id: str, latency: float, cache_hits: int, tokens_saved: int):
    headers = ["timestamp", "user_id", "latency_seconds", "cache_hits", "tokens_saved"]
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "latency_seconds": latency,
        "cache_hits": cache_hits,
        "tokens_saved": tokens_saved
    }
    append_to_csv("usage_stats.csv", headers, row)
