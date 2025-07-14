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

# Onboarding system classes
class OnboardingModal(discord.ui.Modal, title='Welcome to the Server!'):
    """Modal form for collecting new member information."""
    
    def __init__(self, bot, member):
        super().__init__()
        self.bot = bot
        self.member = member
    
    preferred_name = discord.ui.TextInput(
        label='Preferred Name',
        placeholder='What would you like to be called?',
        required=True,
        max_length=50
    )
    
    gamertag = discord.ui.TextInput(
        label='Gamertag',
        placeholder='Your gaming username/tag',
        required=True,
        max_length=50
    )
    
    birthday_day = discord.ui.TextInput(
        label='Birthday Day',
        placeholder='Day (1-31)',
        required=True,
        max_length=2
    )
    
    birthday_month = discord.ui.TextInput(
        label='Birthday Month',
        placeholder='Month (1-12)',
        required=True,
        max_length=2
    )
    
    birthday_year = discord.ui.TextInput(
        label='Birthday Year',
        placeholder='Year (YYYY)',
        required=True,
        max_length=4
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        try:
            # Validate birthday inputs
            day = int(self.birthday_day.value)
            month = int(self.birthday_month.value)
            year = int(self.birthday_year.value)
            
            if not (1 <= day <= 31):
                raise ValueError("Day must be between 1 and 31")
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12")
            if not (1900 <= year <= 2024):
                raise ValueError("Please enter a valid year")
            
            # Format birthday
            birthday = f"{day:02d}/{month:02d}/{year}"
            
            # Send confirmation to user
            await interaction.response.send_message(
                "✅ Thank you! Your information has been submitted to the administrators for review.", 
                ephemeral=True
            )
            
            # Send admin notification
            await self.send_admin_notification(
                self.preferred_name.value,
                self.gamertag.value,
                birthday
            )
            
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Invalid birthday format: {str(e)}. Please try again.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while processing your information. Please try again.",
                ephemeral=True
            )
            logger.error(f"Error in onboarding modal: {e}")
    
    async def send_admin_notification(self, preferred_name, gamertag, birthday):
        """Send notification to admin channel with member info and action buttons."""
        try:
            # Get the onboarding channel
            channel = self.bot.get_channel(Config.ONBOARDING_CHANNEL_ID)
            if not channel:
                logger.error(f"Onboarding channel {Config.ONBOARDING_CHANNEL_ID} not found")
                return
            
            # Create embed with member information
            embed = discord.Embed(
                title="🆕 New Member Registration",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="Member", value=self.member.mention, inline=True)
            embed.add_field(name="Preferred Name", value=preferred_name, inline=True)
            embed.add_field(name="Gamertag", value=gamertag, inline=True)
            embed.add_field(name="Birthday", value=birthday, inline=True)
            embed.add_field(name="Account Created", value=discord.utils.format_dt(self.member.created_at, 'R'), inline=True)
            embed.add_field(name="Joined Server", value=discord.utils.format_dt(self.member.joined_at, 'R'), inline=True)
            
            embed.set_thumbnail(url=self.member.display_avatar.url)
            embed.set_footer(text=f"User ID: {self.member.id}")
            
            # Create view with admin action buttons
            view = AdminApprovalView(self.bot, self.member, preferred_name, gamertag)
            
            # Send message with role mention
            role = self.bot.get_guild(self.member.guild.id).get_role(Config.ONBOARDING_ROLE_ID)
            role_mention = role.mention if role else f"<@&{Config.ONBOARDING_ROLE_ID}>"
            
            await channel.send(
                content=f"{role_mention} New member requires approval:",
                embed=embed,
                view=view
            )
            
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")


class AdminApprovalView(discord.ui.View):
    """View with buttons for admin approval actions."""
    
    def __init__(self, bot, member, preferred_name, gamertag):
        super().__init__(timeout=None)  # Persistent view
        self.bot = bot
        self.member = member
        self.preferred_name = preferred_name
        self.gamertag = gamertag
    
    @discord.ui.button(label='Deny', style=discord.ButtonStyle.danger, emoji='❌')
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle deny button click."""
        try:
            # Update embed to show denial
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = "❌ Member Registration Denied"
            embed.add_field(name="Action By", value=interaction.user.mention, inline=True)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Optionally send DM to member about denial
            try:
                await self.member.send(
                    "❌ Your registration has been denied by the administrators. "
                    "Please contact a moderator if you believe this was in error."
                )
            except discord.Forbidden:
                pass  # User has DMs disabled
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing denial: {str(e)}", ephemeral=True)
            logger.error(f"Error in deny button: {e}")
    
    @discord.ui.button(label='Approve', style=discord.ButtonStyle.success, emoji='✅')
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle approve button click."""
        try:
            # Change member nickname
            new_nickname = f"{self.preferred_name} [{self.gamertag}]"
            await self.member.edit(nick=new_nickname)
            
            # Update embed to show approval
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = "✅ Member Registration Approved"
            embed.add_field(name="Action By", value=interaction.user.mention, inline=True)
            embed.add_field(name="New Nickname", value=new_nickname, inline=True)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Send welcome DM to member
            try:
                await self.member.send(
                    f"🎉 Welcome to the server, {self.preferred_name}! "
                    f"Your registration has been approved and your nickname has been set to `{new_nickname}`."
                )
            except discord.Forbidden:
                pass  # User has DMs disabled
                
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to change nicknames.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing approval: {str(e)}", ephemeral=True)
            logger.error(f"Error in approve button: {e}")
    
    @discord.ui.button(label='18+', style=discord.ButtonStyle.secondary, emoji='🔞')
    async def eighteen_plus_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle 18+ button click."""
        try:
            # Change member nickname
            new_nickname = f"{self.preferred_name} [{self.gamertag}]"
            await self.member.edit(nick=new_nickname)
            
            # Update embed to show 18+ approval
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.purple()
            embed.title = "🔞 Member Registration Approved (18+)"
            embed.add_field(name="Action By", value=interaction.user.mention, inline=True)
            embed.add_field(name="New Nickname", value=new_nickname, inline=True)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Send welcome DM to member
            try:
                await self.member.send(
                    f"🎉 Welcome to the server, {self.preferred_name}! "
                    f"Your registration has been approved (18+) and your nickname has been set to `{new_nickname}`."
                )
            except discord.Forbidden:
                pass  # User has DMs disabled
                
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to change nicknames.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing 18+ approval: {str(e)}", ephemeral=True)
            logger.error(f"Error in 18+ button: {e}")



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
        intents.members = True  # Required for member join events
        
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
    
    async def on_member_join(self, member):
        """Handle new member joining the server."""
        try:
            logger.info(f"New member joined: {member} (ID: {member.id}) in guild {member.guild}")
            
            # Create and send onboarding modal to the member via DM
            modal = OnboardingModal(self, member)
            
            # Create a simple view to trigger the modal
            class OnboardingView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                
                @discord.ui.button(label='Complete Registration', style=discord.ButtonStyle.primary, emoji='📝')
                async def start_registration(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_modal(modal)
            
            # Send welcome DM with registration button
            welcome_embed = discord.Embed(
                title=f"Welcome to {member.guild.name}! 🌹",
                description=(
                    "To complete your registration, please click the button below to fill out a short form. "
                    "This helps our administrators verify new members and set up your profile."
                ),
                color=discord.Color.blue()
            )
            welcome_embed.add_field(
                name="What we'll ask for:",
                value="• Your preferred name\n• Your gamertag\n• Your birthday",
                inline=False
            )
            welcome_embed.set_footer(text="This information helps us maintain a safe and welcoming community.")
            
            view = OnboardingView()
            
            try:
                await member.send(embed=welcome_embed, view=view)
                logger.info(f"Sent onboarding message to {member}")
            except discord.Forbidden:
                logger.warning(f"Could not send DM to {member} - DMs may be disabled")
                
                # If we can't DM them, send a message to the general channel
                # This is a fallback - you might want to adjust this based on your server setup
                if member.guild.system_channel:
                    fallback_embed = discord.Embed(
                        title="Registration Required",
                        description=(
                            f"{member.mention}, welcome to the server! "
                            "Please enable DMs and contact a moderator to complete your registration."
                        ),
                        color=discord.Color.orange()
                    )
                    await member.guild.system_channel.send(embed=fallback_embed)
                    
        except Exception as e:
            logger.error(f"Error handling member join for {member}: {e}")
    
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