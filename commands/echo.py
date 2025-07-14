"""
Echo command - Repeats back user input, demonstrating argument handling.
This is an example command showing how to handle user arguments.
"""
import discord
from commands import BaseCommand

class EchoCommand(BaseCommand):
    """Simple echo command that repeats user input."""
    
    @property
    def name(self):
        return "echo"
    
    @property
    def description(self):
        return "Repeat the provided text back to you"
    
    @property
    def aliases(self):
        return ["repeat", "say"]
    
    @property
    def category(self):
        return "Fun"
    
    async def execute(self, ctx, *args):
        """Execute the echo command."""
        if not args:
            await ctx.send("❓ Please provide some text to echo!\n"
                          f"Usage: `{ctx.prefix}echo <text>`")
            return
        
        # Join all arguments into a single message
        message = " ".join(args)
        
        # Limit message length to prevent abuse
        if len(message) > 1000:
            await ctx.send("❌ Message too long! Please keep it under 1000 characters.")
            return
        
        # Create an embed for the echoed message
        embed = discord.Embed(
            title="🔊 Echo",
            description=message,
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

def setup(bot):
    """Setup function called by the command loader."""
    command = EchoCommand(bot)
    command.setup(bot)
    return command