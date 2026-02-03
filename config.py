"""
Configuration management for the Honey-Pot API.
Uses Pydantic settings for type-safe, environment-based configuration.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "Honey-Pot Scam Detection API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered agentic system that detects scam messages and autonomously engages scammers"
    
    # Security
    api_key: str = Field(..., description="API key for authentication")
    allowed_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated or single value)"
    )
    
    # LLM Configuration
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    llm_model: str = Field(
        default="models/gemini-flash-latest",
        description="Gemini model to use"
    )
    llm_temperature: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="LLM temperature for response generation"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=10,
        description="Max requests per minute"
    )
    
    # Session Management
    session_timeout_minutes: int = Field(
        default=30,
        description="Session timeout in minutes"
    )
    session_cleanup_interval_minutes: int = Field(
        default=5,
        description="How often to clean up expired sessions"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: str = Field(
        default="logs/honeypot.log",
        description="Log file path"
    )
    log_max_bytes: int = Field(
        default=10485760,  # 10MB
        description="Max log file size in bytes"
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of log file backups to keep"
    )
    
    # Callback Configuration
    callback_url: str = Field(
        default="https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
        description="URL for final callback"
    )
    callback_timeout: int = Field(
        default=10,
        description="Callback request timeout in seconds"
    )
    callback_retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for callback"
    )
    
    # Detection Configuration
    scam_confidence_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to consider message as scam"
    )
    exit_confidence_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Confidence threshold to exit conversation"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    def get_allowed_origins_list(self) -> list[str]:
        """Parse allowed_origins string into list."""
        if self.allowed_origins == "*":
            return ["*"]
        # Split by comma and strip whitespace
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings: Application settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience function to reload settings (useful for testing)
def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Returns:
        Settings: Fresh settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
