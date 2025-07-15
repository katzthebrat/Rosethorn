"""
Rules command - Displays realm rules with an "I agree" button.
"""
import discord
from discord.ext import commands
from commands import BaseCommand
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RulesView(discord.ui.View):
    """View containing the 'I agree' button for the rules."""
    
    def __init__(self):
        super().__init__(timeout=None)  # No timeout for persistent view
    
    @discord.ui.button(label="I Agree", style=discord.ButtonStyle.green, emoji="✅")
    async def agree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the 'I agree' button click."""
        user = interaction.user
        guild = interaction.guild
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log the agreement
        log_message = f"[{timestamp}] User {user.display_name} ({user.name}#{user.discriminator}, ID: {user.id}) agreed to the rules in server {guild.name} (ID: {guild.id})"
        logger.info(log_message)
        
        # Also print to console for visibility
        print(f"🌹 RULES AGREEMENT: {log_message}")
        
        # Respond to the user
        await interaction.response.send_message(
            f"✅ Thank you {user.mention}! Your agreement to the realm rules has been recorded.",
            ephemeral=True
        )

class RulesCommand(BaseCommand):
    """Command to display realm rules with an agreement button."""
    
    @property
    def name(self):
        return "rules"
    
    @property
    def description(self):
        return "Display the realm rules with an 'I agree' button"
    
    @property
    def category(self):
        return "Moderation"
    
    async def execute(self, ctx, *args):
        """Execute the rules command."""
        
        # Create the rules embed
        embed = discord.Embed(
            title="🌹 Realm Rules",
            color=discord.Color.purple(),
            description="Please read through all the rules carefully before agreeing."
        )
        
        # Add the rules content
        rules_text = """
**1. Building Restrictions**
Do **NOT** build within 1000 blocks of spawn in any direction. If your base is visible from spawn, you are too close and will be asked to move. If necessary, we may relocate structures ourselves.

**2. No Stealing or Griefing**
Theft, destruction, or griefing will **not** be tolerated. Violators **will** be caught and permanently banned—no second chances.

**3. No Spamming**
Avoid excessive messaging in-game or on Discord. Due to varying time zones, responses may be delayed.

**4. Respect Messaging Boundaries**
Do **NOT** DM members without their permission. Use public channels before reaching out. Messaging to incite drama will be dealt with swiftly. Do **NOT** DM admins about open tickets.

**5. Respect Personal Space**
Avoid building too close to others. If you can see another player's base from yours, you're too close. Entering another member's build without permission is prohibited. *Make sure to set up your land claim to protect your base*

**6. Auto Farms Regulations**
All auto farms **must receive admin approval**, be designated for community use, & include a manual on/off switch to prevent lag.

**7. Zero Tolerance for Harassment**
Treat everyone with respect. **Harassment, witch-hunting, racism, sexism, and hate speech are strictly forbidden**—violators will be immediately banned.

**8. Keep Chats Organized**
Use the appropriate channels for discussions. Conversations may be moved if they become overwhelming. We aim to keep the server welcoming and cozy for all members.
        """
        
        embed.add_field(
            name="Core Rules (1-8)",
            value=rules_text.strip(),
            inline=False
        )
        
        # Add the member mode requirements and additional rules
        additional_rules = """
**9. Member Mode Requirements**
To access member mode, you must:
✅ Add your gamertag to the designated channel
✅ Confirm agreement to these rules
✅ Respond to bot DM (can't find it? Message "Thorn")
*Until then, you will remain a visitor.*

**10. Realm Code Sharing**
Sharing the realm code requires admin approval. If you are found to be violating this you will be temporarily kicked from realm. New players must join Discord (or WhatsApp for Spanish members) and agree to the rules. If they do not have either, a screenshot confirming their agreement, along with their gamertag, will be required.

**11. Admin Requests**
Admins will only provide basic building blocks. Support community shops by purchasing resources from fellow players.

**12. Ticket System**
Once a ticket is opened, you have **12 hours** to respond after the latest admin message sent. If there is no response within that timeframe, the ticket will be closed, and a new one must be opened. Do **NOT** DM admins regarding open tickets—they will be handled when available. Opening multiple tickets for admin attention will result in a ban.
        """
        
        embed.add_field(
            name="Additional Rules (9-12)",
            value=additional_rules.strip(),
            inline=False
        )
        
        # Add footer with important note
        embed.add_field(
            name="⚠️ Important Note",
            value="If you violate any of the listed rules, a ticket will be created to review the situation, allowing you the opportunity to explain and present your perspective.",
            inline=False
        )
        
        embed.set_footer(text="By clicking 'I Agree', you confirm that you have read and understood all rules.")
        
        # Create the view with the button
        view = RulesView()
        
        # Send the embed with the view
        await ctx.send(embed=embed, view=view)

def setup(bot):
    """Setup function called by the command loader."""
    command = RulesCommand(bot)
    command.setup(bot)
    return command