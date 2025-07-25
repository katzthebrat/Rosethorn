import discord
from discord.ext import commands
from datetime import datetime, timedelta
import config
from utils import format_currency, format_datetime

class CheckInCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='checkin', aliases=['ci', 'daily'])
    async def daily_checkin(self, ctx):
        """Perform daily check-in"""
        guild_config = await self.bot.db_service.get_guild_config(ctx.guild.id)
        base_reward = guild_config.daily_reward if guild_config else 100
        
        result, error = await self.bot.economy_service.daily_reward(
            ctx.author.id, ctx.guild.id, base_reward
        )
        
        if error:
            embed = await self.bot.create_embed(
                "Daily Check-In",
                f"Alas, {error.lower()}. Return at the next sunrise for thy Gothic bounty."
            )
            embed.add_field(
                name="💡 Tip",
                value="Check-ins reset at midnight UTC. Keep thy streak alive for greater rewards!",
                inline=False
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        # Create beautiful check-in embed
        embed = await self.bot.create_embed(
            "🌹 Daily Gothic Check-In Complete",
            f"Welcome back to our Victorian manor, {ctx.author.mention}! Thy presence graces these Gothic halls once more."
        )
        
        # Main reward info
        embed.add_field(
            name="💰 Daily Bounty",
            value=format_currency(result['reward'] - result['streak_bonus']),
            inline=True
        )
        embed.add_field(
            name="🔥 Current Streak",
            value=f"{result['streak']} days",
            inline=True
        )
        embed.add_field(
            name="🎁 Streak Bonus",
            value=format_currency(result['streak_bonus']),
            inline=True
        )
        
        # Total and balance
        embed.add_field(
            name="💎 Total Earned",
            value=format_currency(result['reward']),
            inline=True
        )
        embed.add_field(
            name="🏦 New Balance",
            value=format_currency(result['new_balance']),
            inline=True
        )
        embed.add_field(
            name="📅 Next Check-In",
            value="Tomorrow at midnight UTC",
            inline=True
        )
        
        # Streak milestone rewards
        if result['streak'] in [7, 14, 30, 60, 100]:
            embed.add_field(
                name="🏆 Milestone Achieved!",
                value=f"Congratulations on reaching {result['streak']} days! Extra rewards await thee.",
                inline=False
            )
        
        # Motivational messages based on streak
        if result['streak'] == 1:
            embed.set_footer(text="🌱 Thy Gothic journey begins anew!")
        elif result['streak'] < 7:
            embed.set_footer(text="🕯️ Keep the flame of dedication burning!")
        elif result['streak'] < 30:
            embed.set_footer(text="⚡ Thy dedication to the manor grows stronger!")
        else:
            embed.set_footer(text="👑 A true noble of the Gothic realm!")
        
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        
        # Send XP reward
        xp_result = await self.bot.db_service.update_user_xp(ctx.author.id, 25)
        if xp_result and xp_result['level_up']:
            level_embed = await self.bot.create_embed(
                "🎉 Level Up!",
                f"Thy dedication has elevated thee to **Level {xp_result['level']}**!"
            )
            level_embed.add_field(
                name="📈 Experience Points",
                value=f"{xp_result['xp']:,} XP",
                inline=True
            )
            await ctx.send(embed=level_embed)
    
    @commands.command(name='streak', aliases=['streaks'])
    async def check_streak(self, ctx, member: discord.Member = None):
        """Check check-in streak"""
        target = member or ctx.author
        
        # Get latest check-in
        latest_checkin = await self.bot.db_service.get_latest_checkin(target.id, ctx.guild.id)
        
        if not latest_checkin:
            embed = await self.bot.create_embed(
                f"Check-In Status for {target.display_name}",
                "This noble soul has not yet begun their Gothic journey. Use `r!checkin` to start!"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if streak is still active
        today = datetime.utcnow().date()
        last_checkin_date = latest_checkin.date.date()
        days_since = (today - last_checkin_date).days
        
        if days_since == 0:
            status = "✅ Checked in today"
            current_streak = latest_checkin.streak
        elif days_since == 1:
            status = "⚠️ Haven't checked in today"
            current_streak = latest_checkin.streak
        else:
            status = "❌ Streak broken"
            current_streak = 0
        
        embed = await self.bot.create_embed(
            f"🔥 Gothic Streak for {target.display_name}",
            f"Behold the dedication of this noble soul..."
        )
        embed.add_field(
            name="Current Status",
            value=status,
            inline=True
        )
        embed.add_field(
            name="Current Streak",
            value=f"{current_streak} days",
            inline=True
        )
        embed.add_field(
            name="Last Check-In",
            value=format_datetime(latest_checkin.date),
            inline=True
        )
        
        if latest_checkin.mood:
            embed.add_field(
                name="Last Mood",
                value=latest_checkin.mood,
                inline=True
            )
        
        # Streak statistics
        total_checkins = await self.bot.db_service.get_total_checkins(target.id, ctx.guild.id)
        embed.add_field(
            name="Total Check-Ins",
            value=f"{total_checkins} times",
            inline=True
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(name='checkinboard', aliases=['streakboard', 'cb'])
    async def checkin_leaderboard(self, ctx):
        """Show check-in leaderboard"""
        top_streaks = await self.bot.db_service.get_checkin_leaderboard(ctx.guild.id, 'streak', 10)
        top_total = await self.bot.db_service.get_checkin_leaderboard(ctx.guild.id, 'total', 10)
        
        embed = await self.bot.create_embed(
            "🏆 Gothic Check-In Champions",
            "Behold the most dedicated souls of our Victorian manor!"
        )
        
        # Current streaks leaderboard
        streak_text = ""
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, (user_id, streak) in enumerate(top_streaks):
            user = ctx.guild.get_member(int(user_id))
            username = user.display_name if user else "Unknown User"
            streak_text += f"{emojis[i]} **{username}** - {streak} days\n"
        
        if streak_text:
            embed.add_field(
                name="🔥 Current Streaks",
                value=streak_text,
                inline=True
            )
        
        # Total check-ins leaderboard
        total_text = ""
        for i, (user_id, total) in enumerate(top_total):
            user = ctx.guild.get_member(int(user_id))
            username = user.display_name if user else "Unknown User"
            total_text += f"{emojis[i]} **{username}** - {total} check-ins\n"
        
        if total_text:
            embed.add_field(
                name="📊 Total Check-Ins",
                value=total_text,
                inline=True
            )
        
        # Server statistics
        total_checkins_today = await self.bot.db_service.get_checkins_today(ctx.guild.id)
        active_streaks = await self.bot.db_service.get_active_streaks(ctx.guild.id)
        
        embed.add_field(
            name="📈 Server Stats",
            value=f"**Today's Check-Ins:** {total_checkins_today}\n**Active Streaks:** {active_streaks}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mood')
    async def set_mood(self, ctx, *, mood=None):
        """Set mood for today's check-in"""
        if not mood:
            embed = await self.bot.create_embed(
                "Gothic Moods",
                "How dost thou feel in our Victorian manor today?"
            )
            embed.add_field(
                name="🎭 Available Moods",
                value="• Mysterious 🌙\n• Elegant 🌹\n• Melancholic 🥀\n• Inspired ✨\n• Contemplative 🕯️\n• Dramatic 🎪\n• Romantic 💕\n• Mischievous 😈",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}mood <your_mood>`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Update mood for today's check-in
        success = await self.bot.db_service.update_checkin_mood(ctx.author.id, ctx.guild.id, mood)
        
        if success:
            embed = await self.bot.create_embed(
                "🎭 Mood Set",
                f"Thy Gothic mood has been recorded: **{mood}**"
            )
            embed.add_field(
                name="💡 Tip",
                value="Thy mood will be remembered with today's check-in. Set a new mood each day to track thy emotional journey!",
                inline=False
            )
        else:
            embed = await self.bot.create_embed(
                "Mood Setting Failed",
                "Thou must complete thy daily check-in before setting a mood."
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='checkinhistory', aliases=['history'])
    async def checkin_history(self, ctx, member: discord.Member = None, days: int = 30):
        """View check-in history"""
        target = member or ctx.author
        
        if days > 90:
            days = 90
        elif days < 1:
            days = 30
        
        history = await self.bot.db_service.get_checkin_history(target.id, ctx.guild.id, days)
        
        if not history:
            embed = await self.bot.create_embed(
                f"Check-In History for {target.display_name}",
                "No check-in history found for this time period."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            f"📅 Check-In History for {target.display_name}",
            f"Last {days} days of Gothic dedication"
        )
        
        # Group by week
        weeks = {}
        for checkin in history:
            week_start = checkin.date.date() - timedelta(days=checkin.date.weekday())
            if week_start not in weeks:
                weeks[week_start] = []
            weeks[week_start].append(checkin)
        
        for week_start, checkins in sorted(weeks.items(), reverse=True)[:4]:  # Show last 4 weeks
            week_text = ""
            for i in range(7):
                day = week_start + timedelta(days=i)
                checkin = next((c for c in checkins if c.date.date() == day), None)
                
                if checkin:
                    emoji = "✅" if checkin.streak > 0 else "❌"
                    mood_emoji = self.get_mood_emoji(checkin.mood) if checkin.mood else ""
                    week_text += f"{emoji}{mood_emoji} "
                else:
                    week_text += "⭕ "
            
            embed.add_field(
                name=f"Week of {week_start.strftime('%Y-%m-%d')}",
                value=f"`{week_text}`",
                inline=False
            )
        
        embed.add_field(
            name="Legend",
            value="✅ Checked in | ❌ Missed | ⭕ No data",
            inline=False
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    def get_mood_emoji(self, mood):
        """Get emoji for mood"""
        mood_emojis = {
            'mysterious': '🌙',
            'elegant': '🌹',
            'melancholic': '🥀',
            'inspired': '✨',
            'contemplative': '🕯️',
            'dramatic': '🎪',
            'romantic': '💕',
            'mischievous': '😈'
        }
        return mood_emojis.get(mood.lower(), '🎭')

def setup(bot):
    bot.add_cog(CheckInCommands(bot))
