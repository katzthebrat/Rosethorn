"""
Rules command - Shows server rules and guidelines.
"""
import discord
from commands import BaseCommand

class RulesCommand(BaseCommand):
    """Shows server rules and guidelines."""
    
    @property
    def name(self):
        return "rules"
    
    @property
    def description(self):
        return "Display server rules and guidelines"
    
    @property
    def aliases(self):
        return ["rule", "guidelines"]
    
    @property
    def category(self):
        return "Moderation"
    
    async def execute(self, ctx, *args):
        """Execute the rules command."""
        embed = discord.Embed(
            title="📋 Server Rules",
            description="Please read and follow these rules to ensure a positive experience for everyone.",
            color=discord.Color(0x711417)
        )
        
        # General rules section
        embed.add_field(
            name="🔸 General Rules",
            value="• Be respectful to all members\n"
                  "• No harassment, bullying, or discrimination\n"
                  "• Keep discussions civil and on-topic\n"
                  "• No spam or excessive self-promotion",
            inline=False
        )
        
        # Content rules section
        embed.add_field(
            name="🔸 Content Guidelines",
            value="• No NSFW content in public channels\n"
                  "• No sharing of personal information\n"
                  "• No piracy or illegal content\n"
                  "• Use appropriate channels for your content",
            inline=False
        )
        
        # Behavior rules section
        embed.add_field(
            name="🔸 Behavior Expectations",
            value="• Follow Discord's Terms of Service\n"
                  "• Listen to moderator instructions\n"
                  "• Report issues to staff privately\n"
                  "• Use common sense and good judgment",
            inline=False
        )
        
        # Consequences section
        embed.add_field(
            name="⚠️ Consequences",
            value="Violations may result in warnings, temporary mutes, kicks, or permanent bans depending on severity.",
            inline=False
        )
        
        embed.set_footer(text="Thank you for helping keep our server a welcoming place! 🌹")
        
        await ctx.send(embed=embed)

def setup(bot):
    """Setup function called by the command loader."""
    command = RulesCommand(bot)
    command.setup(bot)
    return command