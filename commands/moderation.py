import discord
from discord.ext import commands
from datetime import datetime, timedelta
import config
from utils import parse_duration, format_duration

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        try:
            await member.kick(reason=f"{reason} | Kicked by {ctx.author}")
            
            embed = await self.bot.create_embed(
                "Member Banished",
                f"{member.mention} has been cast out from our Gothic manor.\n**Reason:** {reason}"
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Date", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=True)
            
            await ctx.send(embed=embed)
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'kick', {
                'target': str(member.id),
                'reason': reason
            })
            
        except discord.Forbidden:
            embed = await self.bot.create_embed(
                "Permission Denied",
                "I lack the noble authority to banish this member from our realm."
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, duration=None, *, reason="No reason provided"):
        """Ban a member from the server"""
        try:
            # Parse duration if provided
            unban_at = None
            if duration:
                ban_duration = parse_duration(duration)
                unban_at = datetime.utcnow() + ban_duration
            
            await member.ban(reason=f"{reason} | Banned by {ctx.author}")
            
            embed = await self.bot.create_embed(
                "Member Exiled",
                f"{member.mention} has been permanently exiled from our Gothic domain.\n**Reason:** {reason}"
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            if unban_at:
                embed.add_field(name="Duration", value=format_duration(ban_duration), inline=True)
                embed.add_field(name="Unban Date", value=unban_at.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
            else:
                embed.add_field(name="Duration", value="Permanent", inline=True)
            
            await ctx.send(embed=embed)
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'ban', {
                'target': str(member.id),
                'reason': reason,
                'duration': duration,
                'unban_at': unban_at.isoformat() if unban_at else None
            })
            
        except discord.Forbidden:
            embed = await self.bot.create_embed(
                "Permission Denied",
                "I lack the sovereign power to exile this member from our realm."
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Issue a warning to a member"""
        warning = await self.bot.db_service.add_warning(
            member.id, ctx.guild.id, ctx.author.id, reason
        )
        
        if warning:
            # Get total warnings
            warnings = await self.bot.db_service.get_user_warnings(member.id, ctx.guild.id)
            warning_count = len(warnings)
            
            embed = await self.bot.create_embed(
                "Warning Issued",
                f"{member.mention} has received a formal warning.\n**Reason:** {reason}"
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Total Warnings", value=str(warning_count), inline=True)
            embed.add_field(name="Warning ID", value=str(warning.id), inline=True)
            
            # Auto-escalation
            if warning_count >= 3:
                embed.add_field(
                    name="⚠️ Escalation Notice",
                    value="This member has reached the warning threshold. Consider further action.",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
            # DM the user
            try:
                dm_embed = await self.bot.create_embed(
                    "Warning Received",
                    f"You have received a warning in **{ctx.guild.name}**.\n**Reason:** {reason}\n**Total Warnings:** {warning_count}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass
    
    @commands.command(name='warnings')
    @commands.has_permissions(manage_messages=True)
    async def check_warnings(self, ctx, member: discord.Member = None):
        """Check warnings for a member"""
        target = member or ctx.author
        warnings = await self.bot.db_service.get_user_warnings(target.id, ctx.guild.id)
        
        embed = await self.bot.create_embed(
            f"Warnings for {target.display_name}",
            f"Total active warnings: **{len(warnings)}**"
        )
        
        if warnings:
            for i, warning in enumerate(warnings[-5:], 1):  # Show last 5
                embed.add_field(
                    name=f"Warning #{warning.id}",
                    value=f"**Reason:** {warning.reason}\n**Date:** {warning.created_at.strftime('%Y-%m-%d')}",
                    inline=False
                )
        else:
            embed.description += "\n\nThis noble soul maintains a spotless record! 🌹"
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, duration="1h", *, reason="No reason provided"):
        """Mute a member temporarily"""
        try:
            # Find or create mute role
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if not mute_role:
                mute_role = await ctx.guild.create_role(
                    name="Muted",
                    color=discord.Color.dark_grey(),
                    reason="Auto-created mute role"
                )
                
                # Update permissions for all channels
                for channel in ctx.guild.channels:
                    await channel.set_permissions(
                        mute_role,
                        send_messages=False,
                        speak=False,
                        add_reactions=False
                    )
            
            # Parse duration
            mute_duration = parse_duration(duration)
            unmute_at = datetime.utcnow() + mute_duration
            
            await member.add_roles(mute_role, reason=f"Muted by {ctx.author}: {reason}")
            
            embed = await self.bot.create_embed(
                "Member Silenced",
                f"{member.mention} has been silenced in our Gothic halls.\n**Reason:** {reason}"
            )
            embed.add_field(name="Duration", value=format_duration(mute_duration), inline=True)
            embed.add_field(name="Unmute Time", value=unmute_at.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Schedule unmute (in a real bot, you'd use a task scheduler)
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'mute', {
                'target': str(member.id),
                'reason': reason,
                'duration': duration,
                'unmute_at': unmute_at.isoformat()
            })
            
        except discord.Forbidden:
            embed = await self.bot.create_embed(
                "Permission Denied",
                "I lack the authority to silence this member in our Gothic manor."
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmute a member"""
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if mute_role and mute_role in member.roles:
            await member.remove_roles(mute_role, reason=f"Unmuted by {ctx.author}")
            
            embed = await self.bot.create_embed(
                "Voice Restored",
                f"{member.mention} may once again speak in our Gothic halls."
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'unmute', {
                'target': str(member.id)
            })
        else:
            embed = await self.bot.create_embed(
                "No Action Needed",
                f"{member.mention} is not currently silenced."
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='purge', aliases=['clear'])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, amount: int = 10):
        """Delete multiple messages"""
        if amount > 100:
            embed = await self.bot.create_embed(
                "Limit Exceeded",
                "I cannot purge more than 100 messages at once."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for command message
        
        embed = await self.bot.create_embed(
            "Messages Purged",
            f"Successfully cleared {len(deleted) - 1} messages from this Gothic chamber."
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=5)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'purge', {
            'amount': len(deleted) - 1,
            'channel': str(ctx.channel.id)
        })

def setup(bot):
    bot.add_cog(ModerationCommands(bot))
