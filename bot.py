import os
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import logging
import json
from main import db, create_app
from models import *
from services.discord_service import DiscordService
from services.moderation import ModerationService
from services.economy import EconomyService
from services.tickets import TicketService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'your_discord_bot_token_here')
DEFAULT_PREFIX = '!'
EMBED_COLOR = 0x711417  # Victorian deep red

class RosethornBot(commands.Bot):
    """
    🌹 RosethornBot - A Victorian Gothic themed Discord management bot
    """
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Initialize services
        self.discord_service = DiscordService(self)
        self.moderation = ModerationService(self)
        self.economy = EconomyService(self)
        self.tickets = TicketService(self)
        
        # Create Flask app context for database operations
        self.app = create_app()
        self.app_context = self.app.app_context()
        
    async def get_prefix(self, message):
        """Get command prefix for guild."""
        if not message.guild:
            return DEFAULT_PREFIX
            
        with self.app_context:
            guild_config = Guild.query.filter_by(guild_id=str(message.guild.id)).first()
            return guild_config.prefix if guild_config else DEFAULT_PREFIX
    
    async def setup_hook(self):
        """Setup bot and start background tasks."""
        logger.info("🌹 Setting up RosethornBot...")
        
        # Start the app context
        self.app_context.push()
        
        # Start background tasks
        self.update_member_activity.start()
        self.check_afk_members.start()
        self.process_temporary_punishments.start()
        
        logger.info("🌹 RosethornBot setup complete!")
    
    async def on_ready(self):
        """Bot ready event."""
        logger.info(f"🌹 RosethornBot is online as {self.user}")
        logger.info(f"🌹 Connected to {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="over the Victorian Gothic manor 🌹"
        )
        await self.change_presence(activity=activity)
        
        # Initialize guild configurations
        await self.initialize_guilds()
    
    async def initialize_guilds(self):
        """Initialize configurations for all guilds."""
        for guild in self.guilds:
            with self.app_context:
                guild_config = Guild.query.filter_by(guild_id=str(guild.id)).first()
                if not guild_config:
                    guild_config = Guild(
                        guild_id=str(guild.id),
                        name=guild.name
                    )
                    db.session.add(guild_config)
                    db.session.commit()
                    logger.info(f"🌹 Initialized configuration for guild: {guild.name}")
    
    async def on_guild_join(self, guild):
        """Handle bot joining a new guild."""
        logger.info(f"🌹 Joined new guild: {guild.name} ({guild.id})")
        
        with self.app_context:
            guild_config = Guild(
                guild_id=str(guild.id),
                name=guild.name
            )
            db.session.add(guild_config)
            db.session.commit()
        
        # Send welcome message if possible
        if guild.system_channel:
            embed = discord.Embed(
                title="🌹 Welcome to RosethornBot",
                description="Thank you for inviting me to your Victorian Gothic manor! I am here to serve with elegance and grace.",
                color=EMBED_COLOR
            )
            embed.add_field(
                name="🥀 Getting Started",
                value="Use `!help` to see my commands or visit the web dashboard to configure me.",
                inline=False
            )
            embed.set_footer(text="Crafted with thorns and roses 🌹")
            
            try:
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                pass
    
    async def on_member_join(self, member):
        """Handle member joining guild."""
        await self.discord_service.handle_member_join(member)
    
    async def on_member_remove(self, member):
        """Handle member leaving guild."""
        await self.discord_service.handle_member_leave(member)
    
    async def on_message(self, message):
        """Handle message events."""
        if message.author.bot:
            return
        
        # Update member activity
        await self.discord_service.update_member_activity(message.author, message.guild)
        
        # Check for AFK mentions
        await self.discord_service.check_afk_mentions(message)
        
        # Auto-moderation
        await self.moderation.auto_moderate_message(message)
        
        # Process commands
        await self.process_commands(message)
    
    async def on_message_edit(self, before, after):
        """Log message edits."""
        await self.discord_service.log_message_edit(before, after)
    
    async def on_message_delete(self, message):
        """Log message deletions."""
        await self.discord_service.log_message_delete(message)
    
    @tasks.loop(minutes=5)
    async def update_member_activity(self):
        """Update member activity tracking."""
        for guild in self.guilds:
            for member in guild.members:
                if not member.bot:
                    await self.discord_service.update_member_activity(member, guild)
    
    @tasks.loop(hours=1)
    async def check_afk_members(self):
        """Check for inactive members and mark as AFK."""
        await self.discord_service.check_afk_members()
    
    @tasks.loop(minutes=1)
    async def process_temporary_punishments(self):
        """Process temporary mutes and bans."""
        await self.moderation.process_temporary_punishments()

# Commands
@bot.command(name='help')
async def help_command(ctx):
    """Display help information."""
    embed = discord.Embed(
        title="🌹 RosethornBot Commands",
        description="Your Victorian Gothic servant at your command",
        color=EMBED_COLOR
    )
    
    embed.add_field(
        name="🛡️ Moderation",
        value="`kick`, `ban`, `mute`, `warn`, `warnings`",
        inline=False
    )
    
    embed.add_field(
        name="🌹 Economy",
        value="`balance`, `checkin`, `shop`, `buy`, `daily`",
        inline=False
    )
    
    embed.add_field(
        name="🎫 Tickets",
        value="`ticket`, `close`, `claim`",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Utility",
        value="`afk`, `todo`, `poll`, `embed`",
        inline=False
    )
    
    embed.set_footer(text="Use the web dashboard for advanced configuration 🌹")
    
    await ctx.send(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick_member(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member from the server."""
    await ctx.bot.moderation.kick_member(ctx, member, reason)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member from the server."""
    await ctx.bot.moderation.ban_member(ctx, member, reason)

@bot.command(name='mute')
@commands.has_permissions(manage_messages=True)
async def mute_member(ctx, member: discord.Member, duration: str = None, *, reason="No reason provided"):
    """Mute a member."""
    await ctx.bot.moderation.mute_member(ctx, member, duration, reason)

@bot.command(name='warn')
@commands.has_permissions(manage_messages=True)
async def warn_member(ctx, member: discord.Member, *, reason="No reason provided"):
    """Warn a member."""
    await ctx.bot.moderation.warn_member(ctx, member, reason)

@bot.command(name='balance', aliases=['bal'])
async def check_balance(ctx, member: discord.Member = None):
    """Check currency balance."""
    target = member or ctx.author
    await ctx.bot.economy.check_balance(ctx, target)

@bot.command(name='checkin')
async def daily_checkin(ctx):
    """Daily check-in for currency rewards."""
    await ctx.bot.economy.daily_checkin(ctx)

@bot.command(name='shop')
async def view_shop(ctx):
    """View the server shop."""
    await ctx.bot.economy.view_shop(ctx)

@bot.command(name='buy')
async def buy_item(ctx, *, item_name):
    """Buy an item from the shop."""
    await ctx.bot.economy.buy_item(ctx, item_name)

@bot.command(name='ticket')
async def create_ticket(ctx, *, subject):
    """Create a support ticket."""
    await ctx.bot.tickets.create_ticket(ctx, subject)

@bot.command(name='close')
async def close_ticket(ctx, *, reason="No reason provided"):
    """Close a support ticket."""
    await ctx.bot.tickets.close_ticket(ctx, reason)

@bot.command(name='afk')
async def set_afk(ctx, *, reason="AFK"):
    """Set AFK status."""
    await ctx.bot.discord_service.set_afk(ctx, reason)

@bot.command(name='embed')
@commands.has_permissions(manage_messages=True)
async def create_embed(ctx, *, content):
    """Create a custom embed message."""
    embed = discord.Embed(
        description=content,
        color=EMBED_COLOR
    )
    embed.set_footer(text="Created with RosethornBot 🌹")
    await ctx.send(embed=embed)

@bot.command(name='poll')
async def create_poll(ctx, question, *options):
    """Create a poll with reactions."""
    if len(options) < 2:
        await ctx.send("❌ Please provide at least 2 options for the poll.")
        return
    
    if len(options) > 10:
        await ctx.send("❌ Maximum 10 options allowed.")
        return
    
    embed = discord.Embed(
        title="📊 Poll",
        description=question,
        color=EMBED_COLOR
    )
    
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    for i, option in enumerate(options):
        embed.add_field(
            name=f"{reactions[i]} Option {i+1}",
            value=option,
            inline=False
        )
    
    embed.set_footer(text=f"Poll created by {ctx.author.display_name} 🌹")
    
    poll_message = await ctx.send(embed=embed)
    
    for i in range(len(options)):
        await poll_message.add_reaction(reactions[i])

# Create bot instance
bot = RosethornBot()

async def run_discord_bot():
    """Run the Discord bot."""
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"🥀 Bot startup error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_discord_bot())
