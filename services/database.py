import asyncio
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from models import User, GuildConfig, Command, Warning, Ticket, Application, CheckIn, ShopItem, SocialMonitor, Todo, StickyMessage, AuditLog
from main import db
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for bot operations"""
    
    async def get_or_create_user(self, discord_id, username=None, discriminator=None):
        """Get or create user record"""
        try:
            user = User.query.filter_by(discord_id=str(discord_id)).first()
            if not user:
                user = User(
                    discord_id=str(discord_id),
                    username=username or f"User{discord_id}",
                    discriminator=discriminator or "0001"
                )
                db.session.add(user)
                db.session.commit()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_or_create_user: {e}")
            db.session.rollback()
            return None
    
    async def get_guild_config(self, guild_id):
        """Get guild configuration"""
        try:
            return GuildConfig.query.filter_by(guild_id=str(guild_id)).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_guild_config: {e}")
            return None
    
    async def create_guild_config(self, guild_id, guild_name=None):
        """Create guild configuration"""
        try:
            existing = await self.get_guild_config(guild_id)
            if existing:
                return existing
            
            config = GuildConfig(
                guild_id=str(guild_id),
                guild_name=guild_name or f"Guild {guild_id}"
            )
            db.session.add(config)
            db.session.commit()
            return config
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_guild_config: {e}")
            db.session.rollback()
            return None
    
    async def add_warning(self, user_id, guild_id, moderator_id, reason):
        """Add warning to user"""
        try:
            user = await self.get_or_create_user(user_id)
            warning = Warning(
                user_id=user.id,
                guild_id=str(guild_id),
                moderator_id=str(moderator_id),
                reason=reason
            )
            db.session.add(warning)
            db.session.commit()
            return warning
        except SQLAlchemyError as e:
            logger.error(f"Database error in add_warning: {e}")
            db.session.rollback()
            return None
    
    async def get_user_warnings(self, user_id, guild_id):
        """Get user warnings for guild"""
        try:
            user = await self.get_or_create_user(user_id)
            return Warning.query.filter_by(
                user_id=user.id, 
                guild_id=str(guild_id),
                active=True
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_warnings: {e}")
            return []
    
    async def create_ticket(self, guild_id, channel_id, creator_id, category=None, subject=None):
        """Create new ticket"""
        try:
            user = await self.get_or_create_user(creator_id)
            ticket = Ticket(
                guild_id=str(guild_id),
                channel_id=str(channel_id),
                creator_id=user.id,
                category=category,
                subject=subject
            )
            db.session.add(ticket)
            db.session.commit()
            return ticket
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_ticket: {e}")
            db.session.rollback()
            return None
    
    async def update_ticket_status(self, ticket_id, status, assigned_staff=None):
        """Update ticket status"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if ticket:
                ticket.status = status
                if assigned_staff:
                    ticket.assigned_staff = str(assigned_staff)
                if status == 'closed':
                    ticket.closed_at = datetime.utcnow()
                db.session.commit()
                return ticket
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_ticket_status: {e}")
            db.session.rollback()
        return None
    
    async def create_application(self, guild_id, user_id, app_type, responses):
        """Create new application"""
        try:
            user = await self.get_or_create_user(user_id)
            application = Application(
                guild_id=str(guild_id),
                user_id=user.id,
                type=app_type,
                responses=responses
            )
            db.session.add(application)
            db.session.commit()
            return application
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_application: {e}")
            db.session.rollback()
            return None
    
    async def record_checkin(self, user_id, guild_id, mood=None, message=None):
        """Record daily check-in"""
        try:
            user = await self.get_or_create_user(user_id)
            
            # Check if already checked in today
            today = datetime.utcnow().date()
            existing = CheckIn.query.filter_by(
                user_id=user.id,
                guild_id=str(guild_id)
            ).filter(CheckIn.date >= today).first()
            
            if existing:
                return existing, False  # Already checked in
            
            # Calculate streak
            yesterday = today - timedelta(days=1)
            yesterday_checkin = CheckIn.query.filter_by(
                user_id=user.id,
                guild_id=str(guild_id)
            ).filter(CheckIn.date >= yesterday, CheckIn.date < today).first()
            
            streak = (yesterday_checkin.streak + 1) if yesterday_checkin else 1
            
            # Create check-in record
            checkin = CheckIn(
                user_id=user.id,
                guild_id=str(guild_id),
                streak=streak,
                mood=mood,
                message=message
            )
            db.session.add(checkin)
            db.session.commit()
            
            return checkin, True  # New check-in
        except SQLAlchemyError as e:
            logger.error(f"Database error in record_checkin: {e}")
            db.session.rollback()
            return None, False
    
    async def update_user_currency(self, user_id, amount, operation='add'):
        """Update user currency"""
        try:
            user = await self.get_or_create_user(user_id)
            if operation == 'add':
                user.currency += amount
            elif operation == 'subtract':
                user.currency = max(0, user.currency - amount)
            elif operation == 'set':
                user.currency = amount
            
            db.session.commit()
            return user.currency
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_user_currency: {e}")
            db.session.rollback()
            return None
    
    async def update_user_xp(self, user_id, xp_amount):
        """Update user XP and level"""
        try:
            user = await self.get_or_create_user(user_id)
            user.xp += xp_amount
            
            # Calculate new level
            import math
            new_level = int(math.sqrt(user.xp / 100)) + 1
            old_level = user.level
            user.level = new_level
            
            db.session.commit()
            
            return {
                'xp': user.xp,
                'level': new_level,
                'level_up': new_level > old_level
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_user_xp: {e}")
            db.session.rollback()
            return None
    
    async def update_user_activity(self, user_id):
        """Update user last seen timestamp"""
        try:
            user = await self.get_or_create_user(user_id)
            user.last_seen = datetime.utcnow()
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error in update_user_activity: {e}")
            db.session.rollback()
    
    async def get_custom_commands(self, guild_id):
        """Get custom commands for guild"""
        try:
            return Command.query.filter_by(
                guild_id=str(guild_id),
                enabled=True
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_custom_commands: {e}")
            return []
    
    async def log_action(self, guild_id, user_id, action, details=None):
        """Log action to audit log"""
        try:
            log_entry = AuditLog(
                guild_id=str(guild_id),
                user_id=str(user_id) if user_id else None,
                action=action,
                details=details
            )
            db.session.add(log_entry)
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error in log_action: {e}")
            db.session.rollback()
    
    async def cleanup_old_logs(self, days=30):
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            AuditLog.query.filter(AuditLog.timestamp < cutoff_date).delete()
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error in cleanup_old_logs: {e}")
            db.session.rollback()
    
    async def reset_daily_checkins(self):
        """Reset daily check-in related data"""
        try:
            # This would reset any daily-specific data
            # For now, just log the reset
            await self.log_action('system', None, 'daily_reset', {'date': datetime.utcnow().isoformat()})
        except Exception as e:
            logger.error(f"Error in reset_daily_checkins: {e}")
    
    async def get_leaderboard(self, guild_id, metric='currency', limit=10):
        """Get leaderboard for various metrics"""
        try:
            query = User.query
            
            if metric == 'currency':
                query = query.order_by(User.currency.desc())
            elif metric == 'xp':
                query = query.order_by(User.xp.desc())
            elif metric == 'level':
                query = query.order_by(User.level.desc())
            
            return query.limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_leaderboard: {e}")
            return []
