"""
Help command - Shows available commands and their descriptions.
"""
import discord
from commands import BaseCommand

class HelpCommand(BaseCommand):
    """Custom help command that displays available commands."""
    
    @property
    def name(self):
        return "help"
    
    @property
    def description(self):
        return "Show available commands and their descriptions"
    
    @property
    def aliases(self):
        return ["h", "commands"]
    
    @property
    def category(self):
        return "Utility"
    
    async def execute(self, ctx, *args):
        """Execute the help command."""
        # Get all commands from the bot
        commands_list = []
        
        for command in self.bot.commands:
            if command.name == "help":
                continue  # Skip built-in help to avoid confusion
            
            # Get command info
            name = command.name
            description = getattr(command, 'description', 'No description available')
            aliases = getattr(command, 'aliases', [])
            
            command_info = f"**{name}**"
            if aliases:
                command_info += f" (aliases: {', '.join(aliases)})"
            command_info += f"\n{description}\n"
            
            commands_list.append(command_info)
        
        embed = discord.Embed(
            title="🌹 Rosethorn Commands",
            description="Here are all available commands:",
            color=discord.Color.purple()
        )
        
        if commands_list:
            embed.add_field(
                name="Available Commands",
                value="\n".join(commands_list),
                inline=False
            )
        else:
            embed.add_field(
                name="No Commands",
                value="No commands are currently loaded.",
                inline=False
            )
        
        embed.set_footer(text=f"Use {ctx.prefix}<command> to run a command")
        
        await ctx.send(embed=embed)

def setup(bot):
    """Setup function called by the command loader."""
    command = HelpCommand(bot)
    command.setup(bot)
    return command