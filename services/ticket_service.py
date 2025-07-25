import asyncio
from datetime import datetime, timedelta
from models import Ticket, User
from main import db
import logging

logger = logging.getLogger(__name__)

class TicketService:
    """Ticket management service"""
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    async def get_user_tickets(self, user_id, guild_id, status='open'):
        """Get tickets for a user"""
        try:
            user = await self.db_service.get_or_create_user(user_id)
            return Ticket.query.filter_by(
                creator_id=user.id,
                guild_id=str(guild_id),
                status=status
            ).all()
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    async def get_ticket_by_channel(self, channel_id):
        """Get ticket by channel ID"""
        try:
            return Ticket.query.filter_by(channel_id=str(channel_id)).first()
        except Exception as e:
            logger.error(f"Error getting ticket by channel: {e}")
            return None
    
    async def get_tickets_by_status(self, guild_id, status):
        """Get tickets by status"""
        try:
            return Ticket.query.filter_by(
                guild_id=str(guild_id),
                status=status
            ).order_by(Ticket.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting tickets by status: {e}")
            return []
    
    async def assign_staff(self, ticket_id, staff_id):
        """Assign staff member to ticket"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if ticket:
                ticket.assigned_staff = str(staff_id)
                db.session.commit()
                return ticket
        except Exception as e:
            logger.error(f"Error assigning staff to ticket: {e}")
            db.session.rollback()
        return None
    
    async def update_priority(self, ticket_id, priority):
        """Update ticket priority"""
        try:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if priority.lower() not in valid_priorities:
                return None
            
            ticket = Ticket.query.get(ticket_id)
            if ticket:
                ticket.priority = priority.lower()
                db.session.commit()
                return ticket
        except Exception as e:
            logger.error(f"Error updating ticket priority: {e}")
            db.session.rollback()
        return None
    
    async def add_ticket_note(self, ticket_id, staff_id, note):
        """Add internal note to ticket"""
        try:
            # In a full implementation, this would add to a ticket_notes table
            # For now, we'll log it as an action
            await self.db_service.log_action(
                'ticket_system', 
                str(staff_id), 
                'ticket_note', 
                {
                    'ticket_id': ticket_id,
                    'note': note,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error adding ticket note: {e}")
            return False
    
    async def get_ticket_stats(self, guild_id):
        """Get ticket statistics"""
        try:
            total_tickets = Ticket.query.filter_by(guild_id=str(guild_id)).count()
            open_tickets = Ticket.query.filter_by(guild_id=str(guild_id), status='open').count()
            closed_tickets = Ticket.query.filter_by(guild_id=str(guild_id), status='closed').count()
            
            # Average resolution time for closed tickets
            closed_with_times = Ticket.query.filter_by(
                guild_id=str(guild_id), 
                status='closed'
            ).filter(Ticket.closed_at.isnot(None)).all()
            
            avg_resolution_time = None
            if closed_with_times:
                total_time = sum(
                    (ticket.closed_at - ticket.created_at).total_seconds() 
                    for ticket in closed_with_times
                )
                avg_resolution_time = total_time / len(closed_with_times) / 3600  # Hours
            
            return {
                'total_tickets': total_tickets,
                'open_tickets': open_tickets,
                'closed_tickets': closed_tickets,
                'avg_resolution_hours': round(avg_resolution_time, 2) if avg_resolution_time else None
            }
        except Exception as e:
            logger.error(f"Error getting ticket stats: {e}")
            return {}
    
    async def auto_close_inactive_tickets(self, guild_id, days=7):
        """Auto-close tickets that have been inactive"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # In a real implementation, you'd track last activity
            # For now, we'll just close very old open tickets
            old_tickets = Ticket.query.filter_by(
                guild_id=str(guild_id),
                status='open'
            ).filter(Ticket.created_at < cutoff_date).all()
            
            closed_count = 0
            for ticket in old_tickets:
                ticket.status = 'closed'
                ticket.closed_at = datetime.utcnow()
                closed_count += 1
            
            if closed_count > 0:
                db.session.commit()
                
                await self.db_service.log_action(
                    str(guild_id),
                    None,
                    'auto_close_tickets',
                    {'count': closed_count, 'days': days}
                )
            
            return closed_count
        except Exception as e:
            logger.error(f"Error auto-closing tickets: {e}")
            db.session.rollback()
            return 0
    
    async def get_ticket_categories(self, guild_id):
        """Get available ticket categories"""
        # This would typically be stored in database
        # For now, return default categories
        return [
            {
                'name': 'General Support',
                'description': 'General questions and assistance',
                'emoji': '❓'
            },
            {
                'name': 'Technical Issues',
                'description': 'Bot or server technical problems',
                'emoji': '🔧'
            },
            {
                'name': 'Report User',
                'description': 'Report inappropriate behavior',
                'emoji': '⚠️'
            },
            {
                'name': 'Suggestions',
                'description': 'Ideas and feature requests',
                'emoji': '💡'
            },
            {
                'name': 'Appeals',
                'description': 'Punishment appeals and disputes',
                'emoji': '⚖️'
            }
        ]
    
    async def create_ticket_embed(self, ticket, bot):
        """Create formatted embed for ticket"""
        try:
            creator = await bot.fetch_user(int(ticket.creator.discord_id))
            
            embed = await bot.create_embed(
                f"Ticket #{ticket.id}",
                f"Support ticket information"
            )
            
            embed.add_field(
                name="👤 Creator",
                value=f"{creator.mention}\n{creator} ({creator.id})",
                inline=True
            )
            embed.add_field(
                name="📊 Status",
                value=ticket.status.title(),
                inline=True
            )
            embed.add_field(
                name="⚡ Priority",
                value=ticket.priority.title(),
                inline=True
            )
            
            if ticket.subject:
                embed.add_field(
                    name="📝 Subject",
                    value=ticket.subject,
                    inline=False
                )
            
            if ticket.category:
                embed.add_field(
                    name="📂 Category",
                    value=ticket.category,
                    inline=True
                )
            
            if ticket.assigned_staff:
                try:
                    staff = await bot.fetch_user(int(ticket.assigned_staff))
                    embed.add_field(
                        name="👮 Assigned Staff",
                        value=staff.mention,
                        inline=True
                    )
                except:
                    pass
            
            embed.add_field(
                name="📅 Created",
                value=f"<t:{int(ticket.created_at.timestamp())}:R>",
                inline=True
            )
            
            if ticket.closed_at:
                embed.add_field(
                    name="🔒 Closed",
                    value=f"<t:{int(ticket.closed_at.timestamp())}:R>",
                    inline=True
                )
            
            # Color based on status
            if ticket.status == 'open':
                embed.color = 0x00FF00
            elif ticket.status == 'closed':
                embed.color = 0xFF0000
            else:
                embed.color = 0xFFFF00
            
            return embed
        except Exception as e:
            logger.error(f"Error creating ticket embed: {e}")
            return None
    
    async def notify_staff_new_ticket(self, ticket, bot, guild):
        """Notify staff of new ticket"""
        try:
            guild_config = await self.db_service.get_guild_config(guild.id)
            
            if guild_config and guild_config.staff_channel:
                staff_channel = bot.get_channel(int(guild_config.staff_channel))
                
                if staff_channel:
                    embed = await self.create_ticket_embed(ticket, bot)
                    if embed:
                        embed.title = "🆕 New Support Ticket"
                        embed.add_field(
                            name="🔗 Actions",
                            value=f"Jump to ticket: <#{ticket.channel_id}>",
                            inline=False
                        )
                        
                        await staff_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error notifying staff of new ticket: {e}")
