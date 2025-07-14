"""
Ping command - Tests bot responsiveness and shows latency.
"""
import discord
from commands import BaseCommand

class PingCommand(BaseCommand):
    """Simple ping command to test bot responsiveness."""
    
    @property
    def name(self):
        return "ping"
    
    @property
    def description(self):
        return "Check bot latency and responsiveness"
    
    @property
    def category(self):
        return "Utility"
    
    async def execute(self, ctx, *args):
        """Execute the ping command."""
        latency = round(self.bot.latency * 1000, 2)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: `{latency}ms`",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

def setup(bot):
    """Setup function called by the command loader."""
    command = PingCommand(bot)
    command.setup(bot)
    return command