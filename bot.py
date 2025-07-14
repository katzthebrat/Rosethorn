"""
Main bot class for the Rosethorn Discord Bot.
"""
import discord
from discord.ext import commands
import asyncio
import logging
from config import Config
from utils import create_embed

# Set up logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class RosethornBot(commands.Bot):
    """Main bot class."""
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            description=f"{Config.BOT_NAME} - A gaming Discord bot with role management and interactive features"
        )
        
    async def setup_hook(self):
        """Load cogs and sync commands."""
        logger.info("Setting up bot...")
        
        # Load cogs
        cogs = ['cogs.roles', 'cogs.notifications', 'cogs.games']
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
        
        # Sync commands
        try:
            if Config.GUILD_ID:
                guild = discord.Object(id=Config.GUILD_ID)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to guild {Config.GUILD_ID}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} commands globally")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Game(name=f"{Config.BOT_PREFIX}help | Gaming Bot")
        await self.change_presence(activity=activity)
        
        print(f"\n🌹 {Config.BOT_NAME} v{Config.BOT_VERSION} is ready!")
        print(f"Connected as: {self.user}")
        print(f"Bot ID: {self.user.id}")
        print(f"Guilds: {len(self.guilds)}")
        print(f"Command prefix: {Config.BOT_PREFIX}")
        print("=" * 50)
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Try to send a welcome message to the system channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = create_embed(
                f"Hello {guild.name}! 🌹",
                f"Thanks for adding **{Config.BOT_NAME}**!\n\n" +
                "I'm a gaming Discord bot with features for:\n" +
                "• Role management\n" +
                "• Notifications and announcements\n" +
                "• Interactive gaming commands\n\n" +
                f"Use `{Config.BOT_PREFIX}help` to see all available commands!\n" +
                "Use `/` commands for the best experience.",
                discord.Color.green()
            )
            
            try:
                await guild.system_channel.send(embed=embed)
            except:
                pass  # If we can't send, just continue
    
    async def on_member_join(self, member):
        """Called when a new member joins."""
        logger.info(f"New member joined {member.guild.name}: {member}")
        
        # You could add auto-role assignment here
        # or send welcome messages automatically
        
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        logger.error(f"Command error in {ctx.command}: {error}")
        
        embed = create_embed(
            "Error",
            f"An error occurred: {str(error)}",
            discord.Color.red()
        )
        
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass
    
    async def on_application_command_error(self, interaction, error):
        """Handle application command errors."""
        logger.error(f"Application command error: {error}")
        
        embed = create_embed(
            "Error",
            f"An error occurred while processing your command: {str(error)}",
            discord.Color.red()
        )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

# Add some basic text commands for backwards compatibility
class BasicCommands(commands.Cog):
    """Basic text commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show help information."""
        embed = create_embed(
            f"{Config.BOT_NAME} - Help",
            f"**Prefix:** `{Config.BOT_PREFIX}`\n\n" +
            "**Slash Commands (Recommended):**\n" +
            "• `/createrole` - Create a new role\n" +
            "• `/assignrole` - Assign a role to a user\n" +
            "• `/announce` - Send an announcement\n" +
            "• `/gamealert` - Alert for gaming sessions\n" +
            "• `/dice` - Roll dice\n" +
            "• `/coinflip` - Flip a coin\n" +
            "• `/rps` - Play rock paper scissors\n" +
            "• `/8ball` - Ask the magic 8-ball\n" +
            "• `/trivia` - Start a trivia game\n" +
            "• `/numberguess` - Number guessing game\n\n" +
            f"**Text Commands:**\n" +
            "• `{Config.BOT_PREFIX}help` - Show this help\n" +
            "• `{Config.BOT_PREFIX}info` - Bot information\n" +
            "• `{Config.BOT_PREFIX}ping` - Check bot latency",
            discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='info')
    async def info_command(self, ctx):
        """Show bot information."""
        embed = create_embed(
            f"{Config.BOT_NAME} Information",
            f"**Version:** {Config.BOT_VERSION}\n" +
            f"**Guilds:** {len(self.bot.guilds)}\n" +
            f"**Users:** {len(self.bot.users)}\n" +
            f"**Discord.py Version:** {discord.__version__}\n" +
            f"**Latency:** {round(self.bot.latency * 1000)}ms",
            discord.Color.blue()
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping_command(self, ctx):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        embed = create_embed(
            "🏓 Pong!",
            f"Latency: {latency}ms",
            discord.Color.green()
        )
        await ctx.send(embed=embed)

# Function to create and configure the bot
def create_bot():
    """Create and configure the bot instance."""
    bot = RosethornBot()
    
    # Add basic commands cog
    asyncio.create_task(bot.add_cog(BasicCommands(bot)))
    
    return bot