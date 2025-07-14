"""
Rosethorn Discord Bot - A modular Discord bot with dynamic command loading.

This bot features:
- Modular command structure with separate files
- Dynamic command loading and reloading
- Extensible architecture for easy command addition
- Clean separation of concerns

Created by: katzthebrat
Repository: https://github.com/katzthebrat/Rosethorn
"""

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from command_loader import CommandLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log') if not Config.DEBUG else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RosethornBot(commands.Bot):
    """Main bot class for Rosethorn Discord bot."""
    
    def __init__(self):
        """Initialize the bot with intents and configuration."""
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for commands
        intents.guilds = True
        intents.guild_messages = True
        
        # Initialize bot
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            description=Config.DESCRIPTION,
            intents=intents,
            help_command=None  # We'll use our custom help command
        )
        
        # Initialize command loader
        self.command_loader = CommandLoader(self, Config.COMMANDS_DIR)
        
        # Bot statistics
        self.start_time = None
    
    async def setup_hook(self):
        """Setup hook called when bot is starting up."""
        logger.info("Setting up Rosethorn bot...")
        
        # Load all commands
        loaded_count = self.command_loader.load_all_commands()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        
        logger.info(f"Bot setup complete. Loaded {loaded_count} commands.")
    
    async def on_ready(self):
        """Called when bot is ready and connected."""
        self.start_time = discord.utils.utcnow()
        
        logger.info(f"Bot is ready!")
        logger.info(f"Logged in as: {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} servers")
        logger.info(f"Loaded {len(self.commands)} commands")
        logger.info("------")
        
        # Set bot activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Config.COMMAND_PREFIX}help | Modular Bot"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ Command not found. Use `{Config.COMMAND_PREFIX}help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You don't have permission to use this command.")
        else:
            logger.error(f"Unhandled command error: {error}")
            await ctx.send(f"❌ An unexpected error occurred: `{str(error)}`")
    
    async def on_message(self, message):
        """Process messages and commands."""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Log command usage (if message starts with prefix)
        if message.content.startswith(Config.COMMAND_PREFIX):
            logger.info(f"Command used: {message.content} by {message.author} in {message.guild}")
        
        # Process commands
        await self.process_commands(message)
    
    def reload_commands(self):
        """Reload all commands - useful for development."""
        return self.command_loader.reload_all_commands()

async def main():
    """Main function to run the bot."""
    try:
        # Validate configuration
        Config.validate()
        
        # Create and run bot
        bot = RosethornBot()
        
        logger.info("Starting Rosethorn Discord bot...")
        await bot.start(Config.TOKEN)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure DISCORD_TOKEN is set")
    except discord.LoginFailure:
        logger.error("Failed to login. Please check your Discord token.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Bot shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)