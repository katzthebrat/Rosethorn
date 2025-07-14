"""
Entry point for the Rosethorn Discord Bot.
"""
import asyncio
import sys
from config import Config
from bot import create_bot

def main():
    """Main function to start the bot."""
    try:
        # Validate configuration
        Config.validate()
        
        # Create bot instance
        bot = create_bot()
        
        # Run the bot
        print(f"Starting {Config.BOT_NAME} v{Config.BOT_VERSION}...")
        bot.run(Config.DISCORD_TOKEN)
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()