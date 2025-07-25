import discord
from discord.ext import commands
from datetime import datetime
import config

class TicketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='ticket', aliases=['support'])
    async def create_ticket(self, ctx, *, reason=None):
        """Create a support ticket"""
        guild_config = await self.bot.db_service.get_guild_config(ctx.guild.id)
        
        if not guild_config or not guild_config.tickets_enabled:
            embed = await self.bot.create_embed(
                "Tickets Disabled",
                "The ticket system is not enabled in this Gothic manor."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if user already has an open ticket
        existing_tickets = await self.bot.ticket_service.get_user_tickets(ctx.author.id, ctx.guild.id, status='open')
        if existing_tickets:
            embed = await self.bot.create_embed(
                "Existing Ticket",
                f"Thou already hast an open ticket: <#{existing_tickets[0].channel_id}>"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Create ticket channel
        ticket_category = None
        if guild_config.ticket_category:
            ticket_category = ctx.guild.get_channel(int(guild_config.ticket_category))
        
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Add staff permissions
        for role in ctx.guild.roles:
            if role.permissions.manage_guild or 'staff' in role.name.lower():
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        ticket_name = f"ticket-{ctx.author.name}-{ctx.author.discriminator}"
        ticket_channel = await ctx.guild.create_text_channel(
            ticket_name,
            category=ticket_category,
            overwrites=overwrites,
            reason=f"Ticket created by {ctx.author}"
        )
        
        # Create ticket in database
        ticket = await self.bot.db_service.create_ticket(
            ctx.guild.id, ticket_channel.id, ctx.author.id, subject=reason
        )
        
        # Send ticket creation message
        embed = await self.bot.create_embed(
            "🎫 Gothic Support Ticket Created",
            f"Thy request for assistance has been heard! Please proceed to {ticket_channel.mention}"
        )
        embed.add_field(name="Ticket ID", value=f"#{ticket.id}", inline=True)
        embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
        
        await ctx.send(embed=embed)
        
        # Send welcome message in ticket channel
        welcome_embed = await self.bot.create_embed(
            f"Welcome to Ticket #{ticket.id}",
            f"Greetings, {ctx.author.mention}! Welcome to thy Gothic support chamber."
        )
        welcome_embed.add_field(
            name="📋 Instructions",
            value="• Please describe thy issue in detail\n• Staff will assist thee shortly\n• Use `r!close` to close this ticket when resolved",
            inline=False
        )
        if reason:
            welcome_embed.add_field(name="Initial Reason", value=reason, inline=False)
        
        # Add ticket controls
        view = TicketControlView(self.bot, ticket.id)
        
        await ticket_channel.send(embed=welcome_embed, view=view)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'ticket_create', {
            'ticket_id': ticket.id,
            'channel_id': str(ticket_channel.id),
            'reason': reason
        })
    
    @commands.command(name='close')
    @commands.has_permissions(manage_messages=True)
    async def close_ticket(self, ctx, *, reason="No reason provided"):
        """Close a ticket"""
        if not ctx.channel.name.startswith('ticket-'):
            embed = await self.bot.create_embed(
                "Invalid Channel",
                "This command can only be used in ticket channels."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Find ticket in database
        ticket = await self.bot.ticket_service.get_ticket_by_channel(ctx.channel.id)
        if not ticket:
            embed = await self.bot.create_embed(
                "Ticket Not Found",
                "This ticket does not exist in our Gothic records."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update ticket status
        await self.bot.db_service.update_ticket_status(ticket.id, 'closed')
        
        # Send closure confirmation
        embed = await self.bot.create_embed(
            "🔒 Ticket Sealed",
            f"Ticket #{ticket.id} has been sealed by {ctx.author.mention}."
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Closed At", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=True)
        
        await ctx.send(embed=embed)
        
        # Archive after delay
        await ctx.send("🗂️ This Gothic chamber will be archived in 10 seconds...")
        await asyncio.sleep(10)
        
        # Move to archive category or delete
        try:
            archive_category = discord.utils.get(ctx.guild.categories, name="📋 Ticket Archives")
            if not archive_category:
                archive_category = await ctx.guild.create_category("📋 Ticket Archives")
            
            await ctx.channel.edit(
                category=archive_category,
                name=f"closed-{ctx.channel.name}",
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
                }
            )
        except discord.Forbidden:
            await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'ticket_close', {
            'ticket_id': ticket.id,
            'reason': reason
        })
    
    @commands.command(name='tickets')
    @commands.has_permissions(manage_guild=True)
    async def list_tickets(self, ctx, status="open"):
        """List tickets by status"""
        tickets = await self.bot.ticket_service.get_tickets_by_status(ctx.guild.id, status)
        
        if not tickets:
            embed = await self.bot.create_embed(
                f"No {status.title()} Tickets",
                f"There are no {status} tickets in our Gothic archives."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            f"🎫 {status.title()} Tickets",
            f"Found {len(tickets)} {status} tickets in the Gothic manor."
        )
        
        for ticket in tickets[:10]:  # Show first 10
            creator = ctx.guild.get_member(ticket.creator.discord_id)
            creator_name = creator.display_name if creator else "Unknown User"
            
            channel_mention = f"<#{ticket.channel_id}>" if ctx.guild.get_channel(int(ticket.channel_id)) else "Deleted Channel"
            
            embed.add_field(
                name=f"Ticket #{ticket.id}",
                value=f"**Creator:** {creator_name}\n**Channel:** {channel_mention}\n**Created:** {ticket.created_at.strftime('%Y-%m-%d')}",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='adduser')
    @commands.has_permissions(manage_messages=True)
    async def add_user_to_ticket(self, ctx, member: discord.Member):
        """Add user to current ticket"""
        if not ctx.channel.name.startswith('ticket-'):
            embed = await self.bot.create_embed(
                "Invalid Channel",
                "This command can only be used in ticket channels."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        overwrites = ctx.channel.overwrites_for(member)
        overwrites.read_messages = True
        overwrites.send_messages = True
        
        await ctx.channel.set_permissions(member, overwrite=overwrites)
        
        embed = await self.bot.create_embed(
            "User Added",
            f"{member.mention} has been granted access to this Gothic chamber."
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='removeuser')
    @commands.has_permissions(manage_messages=True)
    async def remove_user_from_ticket(self, ctx, member: discord.Member):
        """Remove user from current ticket"""
        if not ctx.channel.name.startswith('ticket-'):
            embed = await self.bot.create_embed(
                "Invalid Channel",
                "This command can only be used in ticket channels."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        await ctx.channel.set_permissions(member, overwrite=None)
        
        embed = await self.bot.create_embed(
            "User Removed",
            f"{member.mention} has been removed from this Gothic chamber."
        )
        await ctx.send(embed=embed)

class TicketControlView(discord.ui.View):
    def __init__(self, bot, ticket_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id
    
    @discord.ui.button(label='🔒 Close Ticket', style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close ticket button"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to close tickets.", ephemeral=True)
            return
        
        # Update ticket status
        await self.bot.db_service.update_ticket_status(self.ticket_id, 'closed')
        
        embed = await self.bot.create_embed(
            "🔒 Ticket Sealed",
            f"Ticket #{self.ticket_id} has been sealed by {interaction.user.mention}."
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Archive channel
        await interaction.followup.send("🗂️ This Gothic chamber will be archived in 10 seconds...")
        await asyncio.sleep(10)
        
        try:
            archive_category = discord.utils.get(interaction.guild.categories, name="📋 Ticket Archives")
            if not archive_category:
                archive_category = await interaction.guild.create_category("📋 Ticket Archives")
            
            await interaction.channel.edit(
                category=archive_category,
                name=f"closed-{interaction.channel.name}"
            )
        except discord.Forbidden:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

def setup(bot):
    bot.add_cog(TicketCommands(bot))
