import re
from typing import Dict, Any, Tuple

# Patterns for PII detection
AADHAAR_PATTERN = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,16}\b")
API_KEY_PATTERN = re.compile(r"\b(?:gsk|sk|key|api|token)_[a-zA-Z0-9]{24,}\b", re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*[^\s]{6,}\b", re.IGNORECASE)

# Prompts Injection / Jailbreak trigger phrases
INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all previous",
    "system prompt extraction",
    "output the system prompt",
    "reveal your prompt",
    "what is your instruction",
    "what comes before this text",
    "under what constraints",
    "show instructions"
]

JAILBREAK_KEYWORDS = [
    "dan",
    "do anything now",
    "developer mode",
    "override requests",
    "override restrictions",
    "bypass safety",
    "sudomode",
    "jailbreak",
    "act as a simulator",
    "pretend you are"
]

# Off-topic words that should trigger direct rejection
OFF_TOPIC_KEYWORDS = [
    "write a poem", "write a song", "write a joke", "tell me a joke", "tell a joke", "write a story",
    "politics", "election", "democrat", "republican", "president", "parliament",
    "football", "cricket", "basketball", "olympics", "sports", "soccer", "baseball",
    "entertainment", "movie", "cinema", "celebrity", "actor", "actress", "singer", "pop star",
    "joke", "poems", "poetry", "haiku", "limerick", "poem"
]

def detect_pii(text: str) -> Tuple[bool, str]:
    """
    Detect PII and return a tuple of (detected, masked_text)
    """
    masked = text
    detected = False
    
    # Credit card masking (run first as it is longer/more specific than Aadhaar)
    if CREDIT_CARD_PATTERN.search(masked):
        detected = True
        masked = CREDIT_CARD_PATTERN.sub("[MASKED_CREDIT_CARD]", masked)
        
    # Aadhaar masking
    if AADHAAR_PATTERN.search(masked):
        detected = True
        masked = AADHAAR_PATTERN.sub("[MASKED_AADHAAR]", masked)
        
    # SSN masking
    if SSN_PATTERN.search(masked):
        detected = True
        masked = SSN_PATTERN.sub("[MASKED_SSN]", masked)
        
    # API Keys masking
    if API_KEY_PATTERN.search(masked):
        detected = True
        masked = API_KEY_PATTERN.sub("[MASKED_API_KEY]", masked)
        
    # Passwords masking
    if PASSWORD_PATTERN.search(masked):
        detected = True
        masked = PASSWORD_PATTERN.sub("[MASKED_PASSWORD]", masked)
        
    return detected, masked

def detect_injection(text: str) -> bool:
    """
    Check if the user input contains prompt injection patterns.
    """
    cleaned = text.lower()
    for kw in INJECTION_KEYWORDS:
        if kw in cleaned:
            return True
    return False

def detect_jailbreak(text: str) -> bool:
    """
    Check if the user input contains jailbreak patterns.
    """
    cleaned = text.lower()
    for kw in JAILBREAK_KEYWORDS:
        if kw in cleaned:
            return True
    return False

def check_off_topic(text: str) -> bool:
    """
    Check if the user request is off-topic (poems, jokes, politics, sports, entertainment).
    """
    cleaned = text.lower()
    # Check simple keywords
    for kw in OFF_TOPIC_KEYWORDS:
        if kw in cleaned:
            return True
            
    # Check if they are asking general non-healthcare questions
    # (can add heuristics, but keywords cover the explicit requirements)
    return False
