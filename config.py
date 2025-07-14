"""
Configuration management for the Rosethorn Discord Bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Bot configuration settings."""
    
    # Discord settings
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    
    # Bot settings
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    BOT_NAME = os.getenv('BOT_NAME', 'Rosethorn Gaming Bot')
    BOT_VERSION = os.getenv('BOT_VERSION', '1.0.0')
    
    # Channel settings
    NOTIFICATIONS_CHANNEL_ID = int(os.getenv('NOTIFICATIONS_CHANNEL_ID', 0))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required in environment variables")
        
        if cls.GUILD_ID == 0:
            print("Warning: GUILD_ID not set, bot will work across all guilds")
            
        return True

# Game-related configuration
GAME_COMMANDS = {
    'dice': 'Roll dice with specified sides',
    'coinflip': 'Flip a coin',
    'rps': 'Play rock paper scissors',
    '8ball': 'Ask the magic 8-ball a question'
}

# Role management configuration
ROLE_PERMISSIONS = {
    'admin': ['manage_roles', 'manage_channels', 'kick_members'],
    'moderator': ['manage_messages', 'timeout_members'],
    'gamer': ['use_voice', 'stream']
}