"""
Configuration settings for the Telegram Bot
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BotConfig:
    """Configuration class for the Telegram bot"""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Server Configuration  
    FLASK_SERVER_URL: str = os.getenv("FLASK_SERVER_URL", "http://localhost:5002/upload")
    
    # File Paths
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp/")
    
    # Webhook Configuration (for production deployment)
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    PORT: int = int(os.getenv("PORT", "8443"))
    
    @classmethod
    def ensure_temp_dir(cls) -> None:
        """Ensure temporary directory exists"""
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate that required configuration is present"""
        if not cls.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        if not cls.FLASK_SERVER_URL:
            raise ValueError("FLASK_SERVER_URL environment variable is required")
        
        print(f"✅ Bot Token: {'*' * (len(cls.BOT_TOKEN) - 10) + cls.BOT_TOKEN[-10:]}")
        print(f"✅ Server URL: {cls.FLASK_SERVER_URL}")
        print(f"✅ Temp Directory: {cls.TEMP_DIR}")
