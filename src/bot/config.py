"""
Configuration settings for the Telegram Bot
"""

import os
from typing import Optional

class BotConfig:
    """Configuration class for the Telegram bot"""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "7305586081:AAGnkSchiRv7VvltvW92VqnMO_uiUUaf9NY")
    
    # Server Configuration
    FLASK_SERVER_URL: str = os.getenv("FLASK_SERVER_URL", "http://132.72.107.202:5002/upload")
    
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
