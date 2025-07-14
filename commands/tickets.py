"""
Ticket system command - Discord bot ticket management with embeds and buttons.
"""
import discord
from discord.ext import commands
from discord import app_commands
from commands import BaseCommand
import asyncio
from typing import Optional
import json
import os

# Ticket category channel ID as specified in requirements
TICKET_CATEGORY_ID = 1313028919997239297

class TicketType:
    """Ticket type constants."""
    PERMISSIONS = "permissions"
    GENERAL = "general"
    REPORT = "report"
    DEFENSE = "defense-submission"

class TicketCreationView(discord.ui.View):
    """View with buttons for ticket creation."""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @discord.ui.button(label="Permissions", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def permissions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.PERMISSIONS)
    
    @discord.ui.button(label="General", style=discord.ButtonStyle.secondary, emoji="💬")
    async def general_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.GENERAL)
    
    @discord.ui.button(label="Report", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.REPORT)
    
    @discord.ui.button(label="Defense Submission", style=discord.ButtonStyle.success, emoji="🛡️")
    async def defense_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.DEFENSE)
    
    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        """Create a new ticket channel."""
        try:
            # Get the ticket category
            category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
            if not category:
                await interaction.response.send_message(
                    "❌ Ticket category not found. Please contact an administrator.", 
                    ephemeral=True
                )
                return
            
            # Create ticket channel name
            ticket_name = f"🎟️ | {interaction.user.display_name}-{ticket_type}"
            
            # Check if user already has an open ticket
            existing_ticket = discord.utils.get(
                category.channels, 
                name__startswith=f"🎟️ | {interaction.user.display_name}-"
            )
            
            if existing_ticket:
                await interaction.response.send_message(
                    f"❌ You already have an open ticket: {existing_ticket.mention}", 
                    ephemeral=True
                )
                return
            
            # Create the ticket channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add permissions for admin staff role if it exists
            admin_role = discord.utils.get(interaction.guild.roles, name="option admin staff")
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            ticket_channel = await category.create_text_channel(
                name=ticket_name,
                overwrites=overwrites,
                reason=f"Ticket created by {interaction.user}"
            )
            
            # Create the initial embed and form
            await self.send_initial_message(ticket_channel, interaction.user, ticket_type)
            
            await interaction.response.send_message(
                f"✅ Ticket created: {ticket_channel.mention}", 
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating ticket: {str(e)}", 
                ephemeral=True
            )
    
    async def send_initial_message(self, channel: discord.TextChannel, user: discord.User, ticket_type: str):
        """Send the initial message with user form in the ticket channel."""
        # Create the form embed
        embed = discord.Embed(
            title=f"🎟️ New {ticket_type.replace('-', ' ').title()} Ticket",
            description=f"Hello {user.mention}! Please provide the following information:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 Required Information",
            value=(
                "Please respond with:\n"
                "**1. Preferred Name:** Your preferred name\n"
                "**2. Gamertag:** Your in-game username\n"
                "**3. Issue:** What do you need help with?"
            ),
            inline=False
        )
        
        # Tag admin staff if role exists
        admin_role = discord.utils.get(channel.guild.roles, name="option admin staff")
        content = f"{admin_role.mention if admin_role else '@option admin staff'} - New ticket created"
        
        # Create admin action view
        admin_view = TicketAdminView(user.id, ticket_type)
        
        await channel.send(content=content, embed=embed, view=admin_view)

class TicketAdminView(discord.ui.View):
    """View with admin buttons for ticket management."""
    
    def __init__(self, ticket_creator_id: int, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_creator_id = ticket_creator_id
        self.ticket_type = ticket_type
        self.claimed_by = None
    
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="✋")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Claim the ticket."""
        # Check if user has admin role
        admin_role = discord.utils.get(interaction.guild.roles, name="option admin staff")
        if not admin_role or admin_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You need admin staff permissions to claim tickets.", 
                ephemeral=True
            )
            return
        
        if self.claimed_by:
            await interaction.response.send_message(
                f"❌ This ticket is already claimed by <@{self.claimed_by}>", 
                ephemeral=True
            )
            return
        
        self.claimed_by = interaction.user.id
        button.label = f"Claimed by {interaction.user.display_name}"
        button.disabled = True
        
        embed = discord.Embed(
            title="✅ Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed)
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket with resolution form."""
        # Check if user has admin role
        admin_role = discord.utils.get(interaction.guild.roles, name="option admin staff")
        if not admin_role or admin_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You need admin staff permissions to close tickets.", 
                ephemeral=True
            )
            return
        
        # Show resolution modal
        modal = TicketCloseModal(
            self.ticket_creator_id, 
            self.claimed_by or interaction.user.id, 
            self.ticket_type,
            interaction.channel
        )
        await interaction.response.send_modal(modal)

class TicketCloseModal(discord.ui.Modal, title="Close Ticket"):
    """Modal for collecting ticket resolution information."""
    
    def __init__(self, creator_id: int, claimed_by: int, ticket_type: str, channel: discord.TextChannel):
        super().__init__()
        self.creator_id = creator_id
        self.claimed_by = claimed_by
        self.ticket_type = ticket_type
        self.channel = channel
    
    issue_description = discord.ui.TextInput(
        label="What was the issue?",
        placeholder="Describe what the ticket was about...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    resolution = discord.ui.TextInput(
        label="How was it resolved?",
        placeholder="Describe how the issue was resolved...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission."""
        try:
            # Create transcript (simplified - just get recent messages)
            messages = []
            async for message in self.channel.history(limit=50):
                messages.append(f"{message.author.display_name}: {message.content}")
            
            transcript_content = "\n".join(reversed(messages))
            
            # Create transcript file
            import io
            transcript_file = discord.File(
                fp=io.StringIO(transcript_content),
                filename=f"transcript-{self.channel.name}.txt"
            )
            
            # Create summary embed
            creator = interaction.guild.get_member(self.creator_id)
            claimed_user = interaction.guild.get_member(self.claimed_by)
            
            summary_embed = discord.Embed(
                title="🔒 **CLOSED** Ticket Summary",
                color=discord.Color.red()
            )
            
            summary_embed.add_field(
                name="👤 Opened by",
                value=creator.mention if creator else f"<@{self.creator_id}>",
                inline=True
            )
            
            summary_embed.add_field(
                name="🛠️ Claimed by",
                value=claimed_user.mention if claimed_user else f"<@{self.claimed_by}>",
                inline=True
            )
            
            summary_embed.add_field(
                name="🎟️ Ticket Type",
                value=self.ticket_type.replace('-', ' ').title(),
                inline=True
            )
            
            summary_embed.add_field(
                name="❓ Issue",
                value=self.issue_description.value,
                inline=False
            )
            
            summary_embed.add_field(
                name="✅ Resolution",
                value=self.resolution.value,
                inline=False
            )
            
            summary_embed.set_footer(text=f"Closed by {interaction.user.display_name}")
            summary_embed.timestamp = discord.utils.utcnow()
            
            # Send summary to category channel
            category = self.channel.category
            if category:
                await category.send(embed=summary_embed, file=transcript_file)
            
            await interaction.response.send_message("✅ Ticket closed successfully!")
            
            # Wait a moment then delete the channel
            await asyncio.sleep(5)
            await self.channel.delete(reason=f"Ticket closed by {interaction.user}")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error closing ticket: {str(e)}", ephemeral=True)

class TicketsCommand(BaseCommand):
    """Tickets command for creating and managing support tickets."""
    
    @property
    def name(self):
        return "tickets"
    
    @property
    def description(self):
        return "Manage support tickets (admin only)"
    
    @property
    def category(self):
        return "Tickets"
    
    async def execute(self, ctx, *args):
        """Execute the tickets command (traditional command)."""
        # Check if user has permission (admin staff role)
        admin_role = discord.utils.get(ctx.guild.roles, name="option admin staff")
        if not admin_role or admin_role not in ctx.author.roles:
            await ctx.send("❌ You need admin staff permissions to use this command.")
            return
        
        await self.send_ticket_panel(ctx.channel)
        await ctx.send("✅ Ticket panel sent!")
    
    async def send_ticket_panel(self, channel):
        """Send the ticket creation panel."""
        embed = discord.Embed(
            title="🎟️ Support Ticket System",
            description="Click a button below to create a support ticket:",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🛡️ Permissions", 
            value="For realm permissions issues", 
            inline=True
        )
        embed.add_field(
            name="💬 General", 
            value="For general support", 
            inline=True
        )
        embed.add_field(
            name="⚠️ Report", 
            value="To report a player", 
            inline=True
        )
        embed.add_field(
            name="🛡️ Defense Submission", 
            value="To plead a case against an infraction", 
            inline=False
        )
        
        embed.set_footer(text="Only create one ticket at a time")
        
        view = TicketCreationView()
        await channel.send(embed=embed, view=view)
    
    def setup(self, bot):
        """Setup method called when loading the command."""
        # Add traditional command
        super().setup(bot)
        
        # Add slash command
        @app_commands.command(name="tickets", description="Send the ticket creation panel (admin only)")
        async def tickets_slash(interaction: discord.Interaction):
            # Check if user has permission
            admin_role = discord.utils.get(interaction.guild.roles, name="option admin staff")
            if not admin_role or admin_role not in interaction.user.roles:
                await interaction.response.send_message(
                    "❌ You need admin staff permissions to use this command.", 
                    ephemeral=True
                )
                return
            
            await self.send_ticket_panel(interaction.channel)
            await interaction.response.send_message("✅ Ticket panel sent!", ephemeral=True)
        
        bot.tree.add_command(tickets_slash)

def setup(bot):
    """Setup function called by the command loader."""
    command = TicketsCommand(bot)
    command.setup(bot)
    return command