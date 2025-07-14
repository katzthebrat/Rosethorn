"""
Notification system for the Rosethorn Discord Bot.
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from utils import create_embed
from config import Config

class Notifications(commands.Cog):
    """Cog for managing server notifications and announcements."""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_notifications = {}

    @app_commands.command(name="announce", description="Send an announcement to a channel")
    @app_commands.describe(
        message="The announcement message",
        channel="Channel to send the announcement to (optional, defaults to current channel)",
        mention_role="Role to mention in the announcement (optional)"
    )
    async def announce(self, interaction: discord.Interaction, message: str, 
                      channel: discord.TextChannel = None, mention_role: discord.Role = None):
        """Send an announcement message."""
        if not interaction.user.guild_permissions.manage_messages:
            embed = create_embed(
                "Permission Denied",
                "You don't have permission to send announcements.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_channel = channel or interaction.channel
        
        try:
            embed = create_embed(
                "📢 Announcement",
                message,
                discord.Color.gold()
            )
            embed.set_footer(text=f"Announced by {interaction.user.display_name}")
            
            mention_text = ""
            if mention_role:
                mention_text = mention_role.mention + "\n"
            
            await target_channel.send(content=mention_text, embed=embed)
            
            # Confirm to the user
            confirm_embed = create_embed(
                "Announcement Sent",
                f"Successfully sent announcement to {target_channel.mention}",
                discord.Color.green()
            )
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = create_embed(
                "Permission Error",
                f"I don't have permission to send messages in {target_channel.mention}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_embed(
                "Error",
                f"Failed to send announcement: {str(e)}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="gamealert", description="Send a gaming session alert")
    @app_commands.describe(
        game="The game being played",
        time="Time of the gaming session (e.g., '8 PM EST')",
        description="Additional details about the session"
    )
    async def game_alert(self, interaction: discord.Interaction, game: str, time: str, description: str = None):
        """Send a gaming session alert."""
        embed = create_embed(
            f"🎮 Gaming Session: {game}",
            f"**Time:** {time}\n" +
            (f"**Details:** {description}\n" if description else "") +
            f"**Host:** {interaction.user.mention}\n\n" +
            "React with 🎮 to join!",
            discord.Color.purple()
        )
        
        try:
            message = await interaction.response.send_message(embed=embed)
            # Get the actual message object to add reactions
            msg = await interaction.original_response()
            await msg.add_reaction("🎮")
            await msg.add_reaction("❌")
            
        except Exception as e:
            embed = create_embed(
                "Error",
                f"Failed to send gaming alert: {str(e)}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reminder", description="Set a reminder for yourself or others")
    @app_commands.describe(
        message="What to remind about",
        time_minutes="How many minutes from now to send the reminder",
        user="User to remind (optional, defaults to yourself)"
    )
    async def reminder(self, interaction: discord.Interaction, message: str, 
                      time_minutes: int, user: discord.Member = None):
        """Set a reminder."""
        if time_minutes < 1 or time_minutes > 10080:  # Max 1 week
            embed = create_embed(
                "Invalid Time",
                "Reminder time must be between 1 minute and 1 week (10080 minutes).",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_user = user or interaction.user
        remind_time = datetime.utcnow() + timedelta(minutes=time_minutes)
        
        # Store the reminder
        reminder_id = f"{interaction.guild.id}_{interaction.user.id}_{remind_time.timestamp()}"
        self.scheduled_notifications[reminder_id] = {
            'user': target_user,
            'message': message,
            'channel': interaction.channel,
            'time': remind_time,
            'sender': interaction.user
        }
        
        # Schedule the reminder
        asyncio.create_task(self._send_reminder(reminder_id))
        
        embed = create_embed(
            "Reminder Set",
            f"I'll remind {target_user.mention} about '{message}' in {time_minutes} minutes.",
            discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    async def _send_reminder(self, reminder_id: str):
        """Send a scheduled reminder."""
        if reminder_id not in self.scheduled_notifications:
            return
            
        reminder_data = self.scheduled_notifications[reminder_id]
        
        # Calculate sleep time
        now = datetime.utcnow()
        sleep_time = (reminder_data['time'] - now).total_seconds()
        
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        
        # Send the reminder
        embed = create_embed(
            "⏰ Reminder",
            f"{reminder_data['user'].mention}\n\n**Reminder:** {reminder_data['message']}\n\n" +
            f"*Set by {reminder_data['sender'].mention}*",
            discord.Color.orange()
        )
        
        try:
            await reminder_data['channel'].send(embed=embed)
        except:
            # If we can't send to the original channel, try to DM the user
            try:
                await reminder_data['user'].send(embed=embed)
            except:
                pass  # If we can't DM either, just skip
        
        # Clean up
        if reminder_id in self.scheduled_notifications:
            del self.scheduled_notifications[reminder_id]

    @app_commands.command(name="serverstats", description="Show server statistics")
    async def server_stats(self, interaction: discord.Interaction):
        """Show server statistics."""
        guild = interaction.guild
        
        # Calculate member statistics
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots
        
        # Channel statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Role statistics
        roles = len(guild.roles) - 1  # Exclude @everyone
        
        embed = create_embed(
            f"📊 {guild.name} Statistics",
            f"**Members:** {total_members}\n" +
            f"**Online:** {online_members}\n" +
            f"**Humans:** {humans}\n" +
            f"**Bots:** {bots}\n\n" +
            f"**Text Channels:** {text_channels}\n" +
            f"**Voice Channels:** {voice_channels}\n" +
            f"**Categories:** {categories}\n\n" +
            f"**Roles:** {roles}\n" +
            f"**Server Created:** {guild.created_at.strftime('%B %d, %Y')}",
            discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="welcome", description="Send a welcome message to new members")
    @app_commands.describe(
        user="The user to welcome",
        custom_message="Custom welcome message (optional)"
    )
    async def welcome(self, interaction: discord.Interaction, user: discord.Member, custom_message: str = None):
        """Send a welcome message to a user."""
        if not interaction.user.guild_permissions.manage_messages:
            embed = create_embed(
                "Permission Denied",
                "You don't have permission to send welcome messages.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        default_message = f"Welcome to **{interaction.guild.name}**, {user.mention}! 🎉\n\n" + \
                         "We're glad to have you here. Check out the channels and don't forget to read the rules!"
        
        message_content = custom_message or default_message
        
        embed = create_embed(
            "🎉 Welcome!",
            message_content,
            discord.Color.green()
        )
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Notifications(bot))