import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./finance.db")
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "financial-health-agent")
    
    # Email Settings
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_TO: str = os.getenv("EMAIL_TO", os.getenv("EMAIL_USER", ""))
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    
    # Model Configurations
    FAST_MODEL: str = "llama-3.1-8b-instant"
    REASONING_MODEL: str = "llama-3.3-70b-versatile"
    FALLBACK_MODEL: str = "gemma2-9b-it"
    
    # Local Guardrail Configurations
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    
    # Network Ollama Fallback (LAN server)
    LOCAL_OLLAMA_URL: str = os.getenv("LOCAL_OLLAMA_URL", "http://192.168.1.22:11434")
    
    # Retry Limits
    MAX_RETRIES: int = 3
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
