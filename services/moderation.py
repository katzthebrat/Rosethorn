import discord
from datetime import datetime, timedelta
from main import db
from models import Member, Warning, BotLog
import re
import logging

logger = logging.getLogger(__name__)

class ModerationService:
    """Moderation and auto-moderation functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Auto-moderation settings
        self.spam_threshold = 5  # messages
        self.spam_timeframe = 10  # seconds
        self.caps_threshold = 0.7  # 70% caps
        self.repeated_chars_threshold = 5
        
        # Track user message history for spam detection
        self.user_message_history = {}
    
    async def auto_moderate_message(self, message):
        """Automatically moderate messages."""
        if message.author.bot or not message.guild:
            return
        
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        now = datetime.utcnow()
        
        # Initialize message history for user
        if user_id not in self.user_message_history:
            self.user_message_history[user_id] = []
        
        # Add current message to history
        self.user_message_history[user_id].append({
            'content': message.content,
            'timestamp': now,
            'channel_id': message.channel.id
        })
        
        # Clean old messages from history
        cutoff_time = now - timedelta(seconds=self.spam_timeframe)
        self.user_message_history[user_id] = [
            msg for msg in self.user_message_history[user_id]
            if msg['timestamp'] > cutoff_time
        ]
        
        # Check for violations
        violations = []
        
        # Spam detection
        if await self.check_spam(user_id, message.channel.id):
            violations.append("spam")
        
        # Excessive caps
        if await self.check_excessive_caps(message.content):
            violations.append("excessive_caps")
        
        # Repeated characters
        if await self.check_repeated_chars(message.content):
            violations.append("repeated_chars")
        
        # Word filter (implement your banned words)
        if await self.check_banned_words(message.content):
            violations.append("banned_words")
        
        # Take action if violations found
        if violations:
            await self.handle_auto_moderation(message, violations)
    
    async def check_spam(self, user_id, channel_id):
        """Check if user is spamming."""
        if user_id not in self.user_message_history:
            return False
        
        recent_messages = self.user_message_history[user_id]
        
        # Check message count in timeframe
        if len(recent_messages) >= self.spam_threshold:
            return True
        
        # Check for repeated content
        contents = [msg['content'] for msg in recent_messages]
        if len(set(contents)) == 1 and len(contents) >= 3:
            return True
        
        return False
    
    async def check_excessive_caps(self, content):
        """Check for excessive capital letters."""
        if len(content) < 10:  # Don't check short messages
            return False
        
        caps_count = sum(1 for c in content if c.isupper())
        total_letters = sum(1 for c in content if c.isalpha())
        
        if total_letters == 0:
            return False
        
        caps_ratio = caps_count / total_letters
        return caps_ratio > self.caps_threshold
    
    async def check_repeated_chars(self, content):
        """Check for repeated characters."""
        pattern = r'(.)\1{' + str(self.repeated_chars_threshold) + ',}'
        return bool(re.search(pattern, content))
    
    async def check_banned_words(self, content):
        """Check for banned words/phrases."""
        # Implement your banned words list
        banned_words = [
            # Add your banned words here
            "spam",
            "badword"  # Example
        ]
        
        content_lower = content.lower()
        return any(word in content_lower for word in banned_words)
    
    async def handle_auto_moderation(self, message, violations):
        """Handle auto-moderation violations."""
        try:
            # Delete the message
            await message.delete()
            
            # Log the violation
            violation_str = ", ".join(violations)
            await self.log_moderation_action(
                guild_id=str(message.guild.id),
                action="auto_moderate",
                target_id=str(message.author.id),
                moderator_id=str(self.bot.user.id),
                reason=f"Auto-moderation: {violation_str}",
                channel_id=str(message.channel.id)
            )
            
            # Send warning to user
            embed = discord.Embed(
                title="🥀 Auto-Moderation",
                description=f"{message.author.mention}, your message was removed for: {violation_str}",
                color=0x711417
            )
            embed.set_footer(text="Please review the server rules 🌹")
            
            warning_msg = await message.channel.send(embed=embed, delete_after=10)
            
            # Add warning to database if serious violation
            if "spam" in violations or "banned_words" in violations:
                await self.add_warning(
                    guild_id=str(message.guild.id),
                    user_id=str(message.author.id),
                    moderator_id=str(self.bot.user.id),
                    reason=f"Auto-moderation: {violation_str}"
                )
        
        except discord.NotFound:
            pass  # Message already deleted
        except discord.Forbidden:
            logger.warning(f"Cannot moderate message in {message.guild.name} - insufficient permissions")
    
    async def kick_member(self, ctx, member, reason):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You cannot kick someone with equal or higher roles.",
                color=0x711417
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Send DM to user before kicking
            try:
                dm_embed = discord.Embed(
                    title="🥀 You have been kicked",
                    description=f"You were kicked from **{ctx.guild.name}**",
                    color=0x711417
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                dm_embed.set_footer(text="You may rejoin the server if you have an invite 🌹")
                
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Kick the member
            await member.kick(reason=f"{reason} | Moderator: {ctx.author}")
            
            # Log the action
            await self.log_moderation_action(
                guild_id=str(ctx.guild.id),
                action="kick",
                target_id=str(member.id),
                moderator_id=str(ctx.author.id),
                reason=reason
            )
            
            # Send confirmation
            embed = discord.Embed(
                title="🥀 Member Kicked",
                description=f"**{member.display_name}** has been kicked from the manor.",
                color=0x711417
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.set_footer(text="Justice served with thorns 🌹")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permission to kick this member.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def ban_member(self, ctx, member, reason):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You cannot ban someone with equal or higher roles.",
                color=0x711417
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Send DM to user before banning
            try:
                dm_embed = discord.Embed(
                    title="🥀 You have been banned",
                    description=f"You were banned from **{ctx.guild.name}**",
                    color=0x711417
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
                dm_embed.set_footer(text="You may appeal this ban by contacting the moderators 🌹")
                
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Ban the member
            await member.ban(reason=f"{reason} | Moderator: {ctx.author}", delete_message_days=1)
            
            # Log the action
            await self.log_moderation_action(
                guild_id=str(ctx.guild.id),
                action="ban",
                target_id=str(member.id),
                moderator_id=str(ctx.author.id),
                reason=reason
            )
            
            # Send confirmation
            embed = discord.Embed(
                title="🥀 Member Banned",
                description=f"**{member.display_name}** has been banished from the manor.",
                color=0x711417
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.set_footer(text="The ban hammer has fallen 🌹")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permission to ban this member.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def mute_member(self, ctx, member, duration, reason):
        """Mute a member."""
        # Create or get muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role:
            # Create muted role
            muted_role = await ctx.guild.create_role(
                name="Muted",
                color=discord.Color.dark_grey(),
                reason="Auto-created by RosethornBot for muting members"
            )
            
            # Set permissions for muted role in all channels
            for channel in ctx.guild.channels:
                await channel.set_permissions(
                    muted_role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False
                )
        
        # Add muted role to member
        try:
            await member.add_roles(muted_role, reason=f"{reason} | Moderator: {ctx.author}")
            
            # Calculate unmute time if duration provided
            unmute_time = None
            if duration:
                duration_delta = self.parse_duration(duration)
                if duration_delta:
                    unmute_time = datetime.utcnow() + duration_delta
            
            # Log the action
            await self.log_moderation_action(
                guild_id=str(ctx.guild.id),
                action="mute",
                target_id=str(member.id),
                moderator_id=str(ctx.author.id),
                reason=reason,
                extra_data={"duration": duration, "unmute_time": unmute_time.isoformat() if unmute_time else None}
            )
            
            # Send confirmation
            embed = discord.Embed(
                title="🤐 Member Muted",
                description=f"**{member.display_name}** has been silenced.",
                color=0x711417
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Duration", value=duration or "Indefinite", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.set_footer(text="Silence falls upon the manor 🌹")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permission to mute this member.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def warn_member(self, ctx, member, reason):
        """Warn a member."""
        # Add warning to database
        await self.add_warning(
            guild_id=str(ctx.guild.id),
            user_id=str(member.id),
            moderator_id=str(ctx.author.id),
            reason=reason
        )
        
        # Get warning count
        with self.bot.app_context:
            warning_count = Warning.query.filter_by(
                guild_id=str(ctx.guild.id),
                user_id=str(member.id),
                active=True
            ).count()
        
        # Send DM to user
        try:
            dm_embed = discord.Embed(
                title="⚠️ Warning Received",
                description=f"You received a warning in **{ctx.guild.name}**",
                color=0x711417
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Moderator", value=str(ctx.author), inline=False)
            dm_embed.add_field(name="Total Warnings", value=str(warning_count), inline=False)
            dm_embed.set_footer(text="Please follow the server rules 🌹")
            
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        # Send confirmation
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            description=f"**{member.display_name}** has been warned.",
            color=0x711417
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warning #", value=str(warning_count), inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.set_footer(text="Warning recorded in the manor's ledger 🌹")
        
        await ctx.send(embed=embed)
        
        # Check for escalating punishments based on warning count
        await self.check_warning_escalation(ctx, member, warning_count)
    
    async def add_warning(self, guild_id, user_id, moderator_id, reason, severity="normal"):
        """Add a warning to the database."""
        with self.bot.app_context:
            warning = Warning(
                guild_id=guild_id,
                user_id=user_id,
                moderator_id=moderator_id,
                reason=reason,
                severity=severity
            )
            db.session.add(warning)
            
            # Update member warning count
            member = Member.query.filter_by(
                user_id=user_id,
                guild_id=guild_id
            ).first()
            
            if member:
                member.warnings += 1
            
            db.session.commit()
    
    async def check_warning_escalation(self, ctx, member, warning_count):
        """Check if escalating punishment is needed based on warning count."""
        if warning_count >= 5:
            # Auto-ban after 5 warnings
            await self.ban_member(ctx, member, "Automatic ban: 5 warnings reached")
        elif warning_count >= 3:
            # Auto-mute for 1 hour after 3 warnings
            await self.mute_member(ctx, member, "1h", "Automatic mute: 3 warnings reached")
    
    async def process_temporary_punishments(self):
        """Process temporary mutes and bans that need to be lifted."""
        # This would be implemented to check for expired punishments
        # and automatically remove them
        pass
    
    def parse_duration(self, duration_str):
        """Parse duration string (e.g., '1h', '30m', '1d') into timedelta."""
        import re
        
        pattern = r'(\d+)([smhd])'
        match = re.match(pattern, duration_str.lower())
        
        if not match:
            return None
        
        amount, unit = match.groups()
        amount = int(amount)
        
        if unit == 's':
            return timedelta(seconds=amount)
        elif unit == 'm':
            return timedelta(minutes=amount)
        elif unit == 'h':
            return timedelta(hours=amount)
        elif unit == 'd':
            return timedelta(days=amount)
        
        return None
    
    async def log_moderation_action(self, guild_id, action, target_id, moderator_id, 
                                  reason, channel_id=None, extra_data=None):
        """Log moderation action to database."""
        with self.bot.app_context:
            log_entry = BotLog(
                guild_id=guild_id,
                level="INFO",
                module="moderation",
                message=f"Moderation action: {action} on user {target_id} by {moderator_id}",
                user_id=target_id,
                channel_id=channel_id,
                extra_data={
                    "action": action,
                    "moderator_id": moderator_id,
                    "reason": reason,
                    **(extra_data or {})
                }
            )
            db.session.add(log_entry)
            db.session.commit()
