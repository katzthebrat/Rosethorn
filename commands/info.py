"""
Info command - Shows information about the bot and server.
"""
import discord
from datetime import datetime
from commands import BaseCommand

class InfoCommand(BaseCommand):
    """Shows bot and server information."""
    
    @property
    def name(self):
        return "info"
    
    @property
    def description(self):
        return "Display bot and server information"
    
    @property
    def aliases(self):
        return ["about", "botinfo"]
    
    @property
    def category(self):
        return "Utility"
    
    async def execute(self, ctx, *args):
        """Execute the info command."""
        embed = discord.Embed(
            title="🌹 Rosethorn Bot Information",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        # Bot information
        embed.add_field(
            name="Bot Info",
            value=f"**Name:** {self.bot.user.name}\n"
                  f"**ID:** {self.bot.user.id}\n"
                  f"**Servers:** {len(self.bot.guilds)}\n"
                  f"**Commands:** {len(self.bot.commands)}",
            inline=True
        )
        
        # Server information (if in a guild)
        if ctx.guild:
            embed.add_field(
                name="Server Info",
                value=f"**Name:** {ctx.guild.name}\n"
                      f"**Members:** {ctx.guild.member_count}\n"
                      f"**Created:** {ctx.guild.created_at.strftime('%Y-%m-%d')}\n"
                      f"**Owner:** {ctx.guild.owner}",
                inline=True
            )
        
        # Technical info
        embed.add_field(
            name="Technical",
            value=f"**Python:** discord.py\n"
                  f"**Latency:** {round(self.bot.latency * 1000, 2)}ms\n"
                  f"**Modular:** ✅ Yes\n"
                  f"**Commands Dir:** commands/",
            inline=True
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.set_footer(text="Rosethorn - Modular Discord Bot")
        
        await ctx.send(embed=embed)

def setup(bot):
    """Setup function called by the command loader."""
    command = InfoCommand(bot)
    command.setup(bot)
    return command