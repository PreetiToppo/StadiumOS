from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "StadiumOS"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Global Rate Limiting Settings
    DEFAULT_RATE_LIMIT: str = "60/minute"
    
    # Heuristics for the Agentic Router
    # If any of these are present in the query, it escalates to the emergency team immediately.
    EMERGENCY_KEYWORDS: List[str] = [
        "fire", "smoke", "bomb", "explosion", "shooting", "shooter", "gun", 
        "terrorist", "attack", "bleeding", "heart attack", "choking", "unconscious",
        "seizure", "collapse", "hostage", "stabbed", "knife", "medical emergency",
        "emergency", "die", "dying", "help me"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
