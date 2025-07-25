import discord
from datetime import datetime
from main import db
from models import Ticket, Guild, BotLog
import logging

logger = logging.getLogger(__name__)

class TicketService:
    """Support ticket system functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Ticket categories and their emoji
        self.ticket_categories = {
            'general': '🎫',
            'support': '🛠️',
            'report': '🚨',
            'appeal': '⚖️',
            'suggestion': '💡',
            'bug': '🐛',
            'other': '❓'
        }
    
    async def create_ticket(self, ctx, subject, category='general'):
        """Create a new support ticket."""
        # Check if user already has an open ticket
        with self.bot.app_context:
            existing_ticket = Ticket.query.filter_by(
                guild_id=str(ctx.guild.id),
                user_id=str(ctx.author.id),
                status='open'
            ).first()
            
            if existing_ticket:
                embed = discord.Embed(
                    title="🎫 Ticket Already Exists",
                    description=f"You already have an open ticket: <#{existing_ticket.channel_id}>",
                    color=0x711417
                )
                embed.set_footer(text="Please use your existing ticket or close it first 🌹")
                await ctx.send(embed=embed, ephemeral=True)
                return
        
        try:
            # Create ticket channel
            guild = ctx.guild
            category_channel = None
            
            # Look for a "Tickets" category
            for cat in guild.categories:
                if 'ticket' in cat.name.lower():
                    category_channel = cat
                    break
            
            # Create channel name
            ticket_name = f"ticket-{ctx.author.name}-{ctx.author.discriminator}"
            
            # Set up permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                )
            }
            
            # Add moderator permissions
            with self.bot.app_context:
                guild_config = Guild.query.filter_by(guild_id=str(guild.id)).first()
                
                if guild_config and guild_config.mod_role:
                    try:
                        mod_role = guild.get_role(int(guild_config.mod_role))
                        if mod_role:
                            overwrites[mod_role] = discord.PermissionOverwrite(
                                read_messages=True,
                                send_messages=True,
                                manage_messages=True,
                                read_message_history=True
                            )
                    except ValueError:
                        pass
            
            # Create the channel
            ticket_channel = await guild.create_text_channel(
                name=ticket_name,
                category=category_channel,
                overwrites=overwrites,
                reason=f"Support ticket created by {ctx.author}"
            )
            
            # Create ticket record in database
            with self.bot.app_context:
                ticket = Ticket(
                    guild_id=str(guild.id),
                    channel_id=str(ticket_channel.id),
                    user_id=str(ctx.author.id),
                    category=category,
                    subject=subject
                )
                db.session.add(ticket)
                db.session.commit()
                
                ticket_id = ticket.id
            
            # Create initial embed message
            embed = discord.Embed(
                title=f"🎫 Support Ticket #{ticket_id}",
                description=f"**Subject:** {subject}",
                color=0x711417
            )
            
            embed.add_field(
                name="👤 Created by",
                value=ctx.author.mention,
                inline=True
            )
            
            embed.add_field(
                name="📋 Category",
                value=f"{self.ticket_categories.get(category, '❓')} {category.title()}",
                inline=True
            )
            
            embed.add_field(
                name="🕐 Status",
                value="🟢 Open",
                inline=True
            )
            
            embed.add_field(
                name="📞 Need Help?",
                value="Our support team will be with you shortly. Please describe your issue in detail.",
                inline=False
            )
            
            embed.set_footer(text="Use !close to close this ticket | Created by RosethornBot 🌹")
            embed.timestamp = datetime.utcnow()
            
            # Send embed and store message ID
            ticket_message = await ticket_channel.send(embed=embed)
            
            # Update ticket with embed message ID
            with self.bot.app_context:
                ticket_record = Ticket.query.get(ticket_id)
                if ticket_record:
                    ticket_record.embed_message_id = str(ticket_message.id)
                    db.session.commit()
            
            # Add control buttons
            view = TicketControlView(self, ticket_id)
            await ticket_channel.send(
                "🎛️ **Ticket Controls:**",
                view=view
            )
            
            # Send confirmation to user
            confirm_embed = discord.Embed(
                title="🎫 Ticket Created",
                description=f"Your support ticket has been created: {ticket_channel.mention}",
                color=0x711417
            )
            confirm_embed.set_footer(text="Please describe your issue in the ticket channel 🌹")
            
            await ctx.send(embed=confirm_embed, ephemeral=True)
            
            # Log ticket creation
            await self.log_ticket_action(
                guild_id=str(guild.id),
                ticket_id=ticket_id,
                action="created",
                user_id=str(ctx.author.id),
                details=f"Subject: {subject}"
            )
            
            logger.info(f"Ticket #{ticket_id} created by {ctx.author} in {guild.name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to create ticket channels.",
                color=0x711417
            )
            embed.add_field(
                name="Required Permissions",
                value="• Manage Channels\n• Manage Permissions\n• Send Messages",
                inline=False
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while creating your ticket. Please try again.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def close_ticket(self, ctx, reason="No reason provided"):
        """Close a support ticket."""
        # Check if command is being used in a ticket channel
        with self.bot.app_context:
            ticket = Ticket.query.filter_by(
                channel_id=str(ctx.channel.id),
                status='open'
            ).first()
            
            if not ticket:
                embed = discord.Embed(
                    title="❌ Not a Ticket Channel",
                    description="This command can only be used in ticket channels.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
                return
            
            # Check permissions
            if (str(ctx.author.id) != ticket.user_id and 
                not ctx.author.guild_permissions.manage_messages):
                embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="Only the ticket creator or moderators can close tickets.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
                return
            
            # Update ticket status
            ticket.status = 'closed'
            ticket.closed_at = datetime.utcnow()
            ticket.closed_by = str(ctx.author.id)
            
            db.session.commit()
            
            ticket_id = ticket.id
            ticket_user_id = ticket.user_id
        
        # Update embed if it exists
        try:
            if ticket.embed_message_id:
                embed_message = await ctx.channel.fetch_message(int(ticket.embed_message_id))
                
                embed = embed_message.embeds[0]
                
                # Update status field
                for i, field in enumerate(embed.fields):
                    if field.name == "🕐 Status":
                        embed.set_field_at(
                            i,
                            name="🕐 Status",
                            value="🔴 Closed",
                            inline=True
                        )
                        break
                
                # Add close information
                embed.add_field(
                    name="🔒 Closed by",
                    value=ctx.author.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Close reason",
                    value=reason,
                    inline=False
                )
                
                embed.color = 0x555555  # Gray color for closed
                
                await embed_message.edit(embed=embed)
        
        except discord.NotFound:
            pass  # Embed message was deleted
        
        # Send close confirmation
        close_embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Support ticket #{ticket_id} has been closed.",
            color=0x711417
        )
        
        close_embed.add_field(
            name="📝 Reason",
            value=reason,
            inline=False
        )
        
        close_embed.add_field(
            name="🔒 Closed by",
            value=ctx.author.mention,
            inline=True
        )
        
        close_embed.add_field(
            name="⏰ This channel will be deleted in 30 seconds",
            value="Save any important information now.",
            inline=False
        )
        
        close_embed.set_footer(text="Thank you for using our support system 🌹")
        
        await ctx.send(embed=close_embed)
        
        # Log ticket closure
        await self.log_ticket_action(
            guild_id=str(ctx.guild.id),
            ticket_id=ticket_id,
            action="closed",
            user_id=str(ctx.author.id),
            details=f"Reason: {reason}"
        )
        
        # Send DM to ticket creator if they didn't close it
        if str(ctx.author.id) != ticket_user_id:
            try:
                user = self.bot.get_user(int(ticket_user_id))
                if user:
                    dm_embed = discord.Embed(
                        title="🔒 Your Ticket Was Closed",
                        description=f"Your support ticket #{ticket_id} in **{ctx.guild.name}** has been closed.",
                        color=0x711417
                    )
                    dm_embed.add_field(name="Reason", value=reason, inline=False)
                    dm_embed.add_field(name="Closed by", value=str(ctx.author), inline=False)
                    dm_embed.set_footer(text="Thank you for contacting support 🌹")
                    
                    await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
        
        # Delete channel after delay
        import asyncio
        await asyncio.sleep(30)
        
        try:
            await ctx.channel.delete(reason=f"Ticket #{ticket_id} closed by {ctx.author}")
        except discord.NotFound:
            pass  # Channel already deleted
        
        logger.info(f"Ticket #{ticket_id} closed by {ctx.author}")
    
    async def claim_ticket(self, ctx):
        """Claim a ticket for assignment."""
        with self.bot.app_context:
            ticket = Ticket.query.filter_by(
                channel_id=str(ctx.channel.id),
                status='open'
            ).first()
            
            if not ticket:
                embed = discord.Embed(
                    title="❌ Not a Ticket Channel",
                    description="This command can only be used in ticket channels.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
                return
            
            if not ctx.author.guild_permissions.manage_messages:
                embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="Only moderators can claim tickets.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
                return
            
            # Update ticket assignment
            ticket.assigned_staff = str(ctx.author.id)
            ticket.status = 'in_progress'
            
            db.session.commit()
            
            ticket_id = ticket.id
        
        # Send claim confirmation
        embed = discord.Embed(
            title="🎯 Ticket Claimed",
            description=f"{ctx.author.mention} has claimed this ticket and will assist you.",
            color=0x711417
        )
        embed.set_footer(text="Our team is here to help 🌹")
        
        await ctx.send(embed=embed)
        
        # Update embed status if it exists
        try:
            if ticket.embed_message_id:
                embed_message = await ctx.channel.fetch_message(int(ticket.embed_message_id))
                
                embed = embed_message.embeds[0]
                
                # Update status field
                for i, field in enumerate(embed.fields):
                    if field.name == "🕐 Status":
                        embed.set_field_at(
                            i,
                            name="🕐 Status",
                            value="🟡 In Progress",
                            inline=True
                        )
                        break
                
                # Add or update assigned staff field
                staff_field_exists = False
                for i, field in enumerate(embed.fields):
                    if field.name == "👨‍💼 Assigned Staff":
                        embed.set_field_at(
                            i,
                            name="👨‍💼 Assigned Staff",
                            value=ctx.author.mention,
                            inline=True
                        )
                        staff_field_exists = True
                        break
                
                if not staff_field_exists:
                    embed.add_field(
                        name="👨‍💼 Assigned Staff",
                        value=ctx.author.mention,
                        inline=True
                    )
                
                embed.color = 0xFFFF00  # Yellow for in progress
                
                await embed_message.edit(embed=embed)
        
        except discord.NotFound:
            pass
        
        # Log ticket claim
        await self.log_ticket_action(
            guild_id=str(ctx.guild.id),
            ticket_id=ticket_id,
            action="claimed",
            user_id=str(ctx.author.id)
        )
        
        logger.info(f"Ticket #{ticket_id} claimed by {ctx.author}")
    
    async def log_ticket_action(self, guild_id, ticket_id, action, user_id, details=None):
        """Log ticket actions to database."""
        with self.bot.app_context:
            log_entry = BotLog(
                guild_id=guild_id,
                level="INFO",
                module="tickets",
                message=f"Ticket #{ticket_id} {action} by user {user_id}",
                user_id=user_id,
                extra_data={
                    "ticket_id": ticket_id,
                    "action": action,
                    "details": details
                }
            )
            db.session.add(log_entry)
            db.session.commit()

class TicketControlView(discord.ui.View):
    """Interactive buttons for ticket control."""
    
    def __init__(self, ticket_service, ticket_id):
        super().__init__(timeout=None)  # Persistent view
        self.ticket_service = ticket_service
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="🎯")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Claim the ticket."""
        ctx = await self.ticket_service.bot.get_context(interaction)
        ctx.author = interaction.user
        ctx.channel = interaction.channel
        ctx.guild = interaction.guild
        
        await self.ticket_service.claim_ticket(ctx)
        await interaction.response.defer()
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket."""
        ctx = await self.ticket_service.bot.get_context(interaction)
        ctx.author = interaction.user
        ctx.channel = interaction.channel
        ctx.guild = interaction.guild
        
        await self.ticket_service.close_ticket(ctx, "Closed via button")
        await interaction.response.defer()
