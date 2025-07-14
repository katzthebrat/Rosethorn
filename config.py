"""
Configuration management for the Rosethorn Discord bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for bot settings."""
    
    # Discord bot token (required)
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    # Command prefix (default: '!')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    
    # Bot description
    DESCRIPTION = os.getenv('BOT_DESCRIPTION', 'Rosethorn - A modular Discord bot')
    
    # Debug mode
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Commands directory
    COMMANDS_DIR = 'commands'
    
    # Onboarding system configuration
    ONBOARDING_CHANNEL_ID = int(os.getenv('ONBOARDING_CHANNEL_ID', '1311529665348767835'))
    ONBOARDING_ROLE_ID = int(os.getenv('ONBOARDING_ROLE_ID', '1308905911489921124'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        if not cls.TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        return True