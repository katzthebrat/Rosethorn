"""
Base command class for the Rosethorn Discord bot.
All commands should inherit from this class for consistency.
"""
from abc import ABC, abstractmethod
from discord.ext import commands
import discord

class BaseCommand(ABC):
    """Abstract base class for all bot commands."""
    
    def __init__(self, bot):
        """Initialize the command with a reference to the bot."""
        self.bot = bot
    
    @property
    @abstractmethod
    def name(self):
        """Return the command name."""
        pass
    
    @property
    @abstractmethod
    def description(self):
        """Return the command description."""
        pass
    
    @property
    def aliases(self):
        """Return command aliases (optional)."""
        return []
    
    @property
    def category(self):
        """Return command category (optional)."""
        return "General"
    
    @abstractmethod
    async def execute(self, ctx, *args):
        """Execute the command logic."""
        pass
    
    def setup(self, bot):
        """Setup method called when loading the command."""
        # Create the discord.py command
        @bot.command(name=self.name, description=self.description, aliases=self.aliases)
        async def command_wrapper(ctx, *args):
            try:
                await self.execute(ctx, *args)
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")
                print(f"Error in command {self.name}: {e}")
        
        # Store reference to the wrapper for cleanup if needed
        self._command_wrapper = command_wrapper