import discord
from datetime import datetime, timedelta, date
from main import db
from models import Member, Guild, BotLog, CheckIn, VoiceSession
import logging

logger = logging.getLogger(__name__)

class DiscordService:
    """Core Discord service functionality."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def update_member_activity(self, member, guild):
        """Update member activity in database."""
        if member.bot:
            return
        
        with self.bot.app_context:
            member_record = Member.query.filter_by(
                user_id=str(member.id),
                guild_id=str(guild.id)
            ).first()
            
            if not member_record:
                member_record = Member(
                    user_id=str(member.id),
                    guild_id=str(guild.id),
                    username=member.display_name or member.name
                )
                db.session.add(member_record)
            
            member_record.last_active = datetime.utcnow()
            member_record.username = member.display_name or member.name
            
            # Clear AFK status if active
            if member_record.is_afk:
                member_record.is_afk = False
                member_record.afk_reason = None
                member_record.afk_since = None
            
            db.session.commit()
    
    async def handle_member_join(self, member):
        """Handle new member joining."""
        guild = member.guild
        
        # Log member join
        await self.log_event(
            guild_id=str(guild.id),
            level="INFO",
            module="member_join",
            message=f"New member joined: {member.display_name} ({member.id})",
            user_id=str(member.id)
        )
        
        # Get guild configuration
        with self.bot.app_context:
            guild_config = Guild.query.filter_by(guild_id=str(guild.id)).first()
            
            if guild_config and guild_config.welcome_channel:
                welcome_channel = guild.get_channel(int(guild_config.welcome_channel))
                
                if welcome_channel:
                    embed = discord.Embed(
                        title="🌹 Welcome to the Manor",
                        description=f"Welcome {member.mention} to our Victorian Gothic sanctuary!",
                        color=0x711417
                    )
                    embed.add_field(
                        name="🥀 Getting Started",
                        value="Please take a moment to read our rules and introduce yourself.",
                        inline=False
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text="May your stay be filled with roses and thorns 🌹")
                    
                    try:
                        await welcome_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
            
            # Create member record
            member_record = Member(
                user_id=str(member.id),
                guild_id=str(guild.id),
                username=member.display_name or member.name
            )
            db.session.add(member_record)
            db.session.commit()
    
    async def handle_member_leave(self, member):
        """Handle member leaving."""
        guild = member.guild
        
        # Log member leave
        await self.log_event(
            guild_id=str(guild.id),
            level="INFO",
            module="member_leave",
            message=f"Member left: {member.display_name} ({member.id})",
            user_id=str(member.id)
        )
        
        # Send goodbye message if configured
        with self.bot.app_context:
            guild_config = Guild.query.filter_by(guild_id=str(guild.id)).first()
            
            if guild_config and guild_config.welcome_channel:
                welcome_channel = guild.get_channel(int(guild_config.welcome_channel))
                
                if welcome_channel:
                    embed = discord.Embed(
                        title="🥀 Farewell",
                        description=f"{member.display_name} has departed from our manor.",
                        color=0x711417
                    )
                    embed.set_footer(text="May they find peace in their journey 🌹")
                    
                    try:
                        await welcome_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
    
    async def log_message_edit(self, before, after):
        """Log message edits."""
        if before.author.bot or before.content == after.content:
            return
        
        await self.log_event(
            guild_id=str(before.guild.id) if before.guild else None,
            level="INFO",
            module="message_edit",
            message=f"Message edited by {before.author} in #{before.channel.name}",
            user_id=str(before.author.id),
            channel_id=str(before.channel.id),
            extra_data={
                "before": before.content[:500],
                "after": after.content[:500],
                "message_id": str(before.id)
            }
        )
    
    async def log_message_delete(self, message):
        """Log message deletions."""
        if message.author.bot:
            return
        
        await self.log_event(
            guild_id=str(message.guild.id) if message.guild else None,
            level="INFO",
            module="message_delete",
            message=f"Message deleted by {message.author} in #{message.channel.name}",
            user_id=str(message.author.id),
            channel_id=str(message.channel.id),
            extra_data={
                "content": message.content[:500],
                "message_id": str(message.id)
            }
        )
    
    async def check_afk_mentions(self, message):
        """Check for AFK member mentions."""
        if not message.mentions:
            return
        
        with self.bot.app_context:
            for mentioned_member in message.mentions:
                member_record = Member.query.filter_by(
                    user_id=str(mentioned_member.id),
                    guild_id=str(message.guild.id)
                ).first()
                
                if member_record and member_record.is_afk:
                    embed = discord.Embed(
                        title="🌙 AFK Member",
                        description=f"{mentioned_member.display_name} is currently away",
                        color=0x711417
                    )
                    
                    if member_record.afk_reason:
                        embed.add_field(
                            name="Reason",
                            value=member_record.afk_reason,
                            inline=False
                        )
                    
                    if member_record.afk_since:
                        embed.add_field(
                            name="Since",
                            value=member_record.afk_since.strftime("%Y-%m-%d %H:%M UTC"),
                            inline=False
                        )
                    
                    await message.channel.send(embed=embed, delete_after=10)
    
    async def set_afk(self, ctx, reason):
        """Set user AFK status."""
        with self.bot.app_context:
            member_record = Member.query.filter_by(
                user_id=str(ctx.author.id),
                guild_id=str(ctx.guild.id)
            ).first()
            
            if not member_record:
                member_record = Member(
                    user_id=str(ctx.author.id),
                    guild_id=str(ctx.guild.id),
                    username=ctx.author.display_name
                )
                db.session.add(member_record)
            
            member_record.is_afk = True
            member_record.afk_reason = reason
            member_record.afk_since = datetime.utcnow()
            
            db.session.commit()
        
        embed = discord.Embed(
            title="🌙 AFK Status Set",
            description=f"{ctx.author.mention} is now away",
            color=0x711417
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="You will be marked as active when you send your next message 🌹")
        
        await ctx.send(embed=embed)
    
    async def check_afk_members(self):
        """Check for members who should be marked as AFK."""
        cutoff_time = datetime.utcnow() - timedelta(days=7)  # Mark as AFK after 7 days
        
        with self.bot.app_context:
            inactive_members = Member.query.filter(
                Member.last_active < cutoff_time,
                Member.is_afk == False
            ).all()
            
            for member in inactive_members:
                member.is_afk = True
                member.afk_reason = "Automatically marked as AFK due to inactivity"
                member.afk_since = member.last_active
            
            if inactive_members:
                db.session.commit()
                logger.info(f"🌙 Marked {len(inactive_members)} members as AFK due to inactivity")
    
    async def log_event(self, guild_id=None, level="INFO", module="general", 
                       message="", user_id=None, channel_id=None, extra_data=None):
        """Log an event to the database."""
        with self.bot.app_context:
            log_entry = BotLog(
                guild_id=guild_id,
                level=level,
                module=module,
                message=message,
                user_id=user_id,
                channel_id=channel_id,
                extra_data=extra_data
            )
            db.session.add(log_entry)
            db.session.commit()
    
    async def get_member_data(self, user_id, guild_id):
        """Get member data from database."""
        with self.bot.app_context:
            return Member.query.filter_by(
                user_id=str(user_id),
                guild_id=str(guild_id)
            ).first()
    
    async def create_or_update_member(self, member, guild):
        """Create or update member record."""
        with self.bot.app_context:
            member_record = Member.query.filter_by(
                user_id=str(member.id),
                guild_id=str(guild.id)
            ).first()
            
            if not member_record:
                member_record = Member(
                    user_id=str(member.id),
                    guild_id=str(guild.id),
                    username=member.display_name or member.name
                )
                db.session.add(member_record)
            else:
                member_record.username = member.display_name or member.name
                member_record.last_active = datetime.utcnow()
            
            db.session.commit()
            return member_record
