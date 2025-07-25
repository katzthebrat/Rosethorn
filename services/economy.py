import discord
from datetime import datetime, date, timedelta
from main import db
from models import Member, Guild, ShopItem, Purchase, CheckIn
import random
import logging

logger = logging.getLogger(__name__)

class EconomyService:
    """Economy system with currency, shop, and rewards."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Check-in rewards
        self.base_checkin_reward = 100
        self.streak_multiplier = 1.1
        self.max_streak_bonus = 500
    
    async def check_balance(self, ctx, member):
        """Check a user's currency balance."""
        with self.bot.app_context:
            guild_config = Guild.query.filter_by(guild_id=str(ctx.guild.id)).first()
            member_data = Member.query.filter_by(
                user_id=str(member.id),
                guild_id=str(ctx.guild.id)
            ).first()
            
            if not member_data:
                member_data = Member(
                    user_id=str(member.id),
                    guild_id=str(ctx.guild.id),
                    username=member.display_name
                )
                db.session.add(member_data)
                db.session.commit()
            
            currency_name = guild_config.currency_name if guild_config else "Roses"
            currency_symbol = guild_config.currency_symbol if guild_config else "🌹"
            
            embed = discord.Embed(
                title=f"💰 {member.display_name}'s Wallet",
                color=0x711417
            )
            
            embed.add_field(
                name=f"{currency_symbol} Balance",
                value=f"{member_data.balance:,} {currency_name}",
                inline=False
            )
            
            embed.add_field(
                name="🌟 Level",
                value=f"Level {member_data.level} ({member_data.xp:,} XP)",
                inline=True
            )
            
            embed.add_field(
                name="🔥 Check-in Streak",
                value=f"{member_data.check_in_streak} days",
                inline=True
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Use daily check-in to earn more rewards 🌹")
            
            await ctx.send(embed=embed)
    
    async def daily_checkin(self, ctx):
        """Handle daily check-in for currency rewards."""
        today = date.today()
        
        with self.bot.app_context:
            guild_config = Guild.query.filter_by(guild_id=str(ctx.guild.id)).first()
            member_data = Member.query.filter_by(
                user_id=str(ctx.author.id),
                guild_id=str(ctx.guild.id)
            ).first()
            
            if not member_data:
                member_data = Member(
                    user_id=str(ctx.author.id),
                    guild_id=str(ctx.guild.id),
                    username=ctx.author.display_name
                )
                db.session.add(member_data)
            
            # Check if already checked in today
            existing_checkin = CheckIn.query.filter_by(
                guild_id=str(ctx.guild.id),
                user_id=str(ctx.author.id),
                date=today
            ).first()
            
            if existing_checkin:
                embed = discord.Embed(
                    title="🌅 Already Checked In",
                    description="You have already checked in today! Come back tomorrow for more rewards.",
                    color=0x711417
                )
                embed.set_footer(text="Patience, dear visitor 🌹")
                await ctx.send(embed=embed)
                return
            
            # Calculate streak
            yesterday = today - timedelta(days=1)
            yesterday_checkin = CheckIn.query.filter_by(
                guild_id=str(ctx.guild.id),
                user_id=str(ctx.author.id),
                date=yesterday
            ).first()
            
            if yesterday_checkin:
                # Continue streak
                new_streak = member_data.check_in_streak + 1
            elif member_data.last_check_in == yesterday:
                # Continue streak (backup check)
                new_streak = member_data.check_in_streak + 1
            else:
                # Reset streak
                new_streak = 1
            
            # Calculate reward
            base_reward = self.base_checkin_reward
            streak_bonus = min(
                int(base_reward * (self.streak_multiplier ** min(new_streak, 30)) - base_reward),
                self.max_streak_bonus
            )
            total_reward = base_reward + streak_bonus
            
            # Add random bonus (5-15% chance for extra reward)
            bonus_chance = random.randint(1, 100)
            bonus_reward = 0
            bonus_message = ""
            
            if bonus_chance <= 5:  # 5% chance for large bonus
                bonus_reward = int(total_reward * random.uniform(0.5, 1.0))
                bonus_message = "✨ **Lucky day!** Extra bonus reward!"
            elif bonus_chance <= 15:  # 10% chance for small bonus
                bonus_reward = int(total_reward * random.uniform(0.1, 0.3))
                bonus_message = "🍀 Small lucky bonus!"
            
            final_reward = total_reward + bonus_reward
            
            # Update member data
            member_data.balance += final_reward
            member_data.check_in_streak = new_streak
            member_data.last_check_in = today
            member_data.xp += 25  # XP for checking in
            
            # Level up check
            level_up_message = ""
            required_xp = member_data.level * 1000
            if member_data.xp >= required_xp:
                member_data.level += 1
                level_up_reward = member_data.level * 50
                member_data.balance += level_up_reward
                level_up_message = f"\n🌟 **Level Up!** You are now level {member_data.level}! (+{level_up_reward} bonus)"
            
            # Create check-in record
            checkin_record = CheckIn(
                guild_id=str(ctx.guild.id),
                user_id=str(ctx.author.id),
                date=today,
                streak=new_streak,
                reward_amount=final_reward
            )
            db.session.add(checkin_record)
            
            db.session.commit()
            
            # Get currency info
            currency_name = guild_config.currency_name if guild_config else "Roses"
            currency_symbol = guild_config.currency_symbol if guild_config else "🌹"
            
            # Create response embed
            embed = discord.Embed(
                title="🌅 Daily Check-in Complete!",
                description=f"Welcome back to the manor, {ctx.author.mention}!",
                color=0x711417
            )
            
            embed.add_field(
                name=f"{currency_symbol} Reward",
                value=f"+{final_reward:,} {currency_name}",
                inline=True
            )
            
            embed.add_field(
                name="🔥 Streak",
                value=f"{new_streak} days",
                inline=True
            )
            
            embed.add_field(
                name="💰 New Balance",
                value=f"{member_data.balance:,} {currency_name}",
                inline=True
            )
            
            if bonus_message:
                embed.add_field(
                    name="🎁 Bonus",
                    value=bonus_message,
                    inline=False
                )
            
            if level_up_message:
                embed.add_field(
                    name="📈 Progress",
                    value=level_up_message.strip(),
                    inline=False
                )
            
            # Streak milestone rewards
            milestone_message = ""
            if new_streak % 7 == 0:  # Weekly milestone
                milestone_reward = 500 + (new_streak // 7) * 100
                member_data.balance += milestone_reward
                db.session.commit()
                milestone_message = f"🎉 **Weekly Milestone!** +{milestone_reward} {currency_name} bonus!"
            elif new_streak % 30 == 0:  # Monthly milestone
                milestone_reward = 2000 + (new_streak // 30) * 500
                member_data.balance += milestone_reward
                db.session.commit()
                milestone_message = f"🏆 **Monthly Milestone!** +{milestone_reward} {currency_name} bonus!"
            
            if milestone_message:
                embed.add_field(
                    name="🎊 Milestone",
                    value=milestone_message,
                    inline=False
                )
            
            embed.set_footer(text="Come back tomorrow for your next reward 🌹")
            
            await ctx.send(embed=embed)
    
    async def view_shop(self, ctx, category=None):
        """Display the server shop."""
        with self.bot.app_context:
            guild_config = Guild.query.filter_by(guild_id=str(ctx.guild.id)).first()
            
            query = ShopItem.query.filter_by(
                guild_id=str(ctx.guild.id),
                purchasable=True
            )
            
            if category:
                query = query.filter_by(category=category)
            
            items = query.order_by(ShopItem.category, ShopItem.price).all()
            
            if not items:
                embed = discord.Embed(
                    title="🏪 Manor Shop",
                    description="The shop is currently empty. Check back later for new items!",
                    color=0x711417
                )
                embed.set_footer(text="Items may be added by administrators 🌹")
                await ctx.send(embed=embed)
                return
            
            currency_name = guild_config.currency_name if guild_config else "Roses"
            currency_symbol = guild_config.currency_symbol if guild_config else "🌹"
            
            # Group items by category
            categories = {}
            for item in items:
                if item.category not in categories:
                    categories[item.category] = []
                categories[item.category].append(item)
            
            embed = discord.Embed(
                title="🏪 Manor Shop",
                description="Welcome to our Victorian collection!",
                color=0x711417
            )
            
            for cat_name, cat_items in categories.items():
                items_text = []
                for item in cat_items[:5]:  # Show max 5 items per category
                    emoji = item.emoji or "📦"
                    stock_text = ""
                    if item.stock > 0:
                        stock_text = f" (Stock: {item.stock})"
                    elif item.stock == 0:
                        stock_text = " (Out of Stock)"
                    
                    rarity_emoji = {
                        'common': '⚪',
                        'uncommon': '🟢', 
                        'rare': '🔵',
                        'epic': '🟣',
                        'legendary': '🟡'
                    }.get(item.rarity, '⚪')
                    
                    items_text.append(
                        f"{emoji} {rarity_emoji} **{item.name}** - {item.price:,} {currency_symbol}{stock_text}"
                    )
                
                if len(cat_items) > 5:
                    items_text.append(f"... and {len(cat_items) - 5} more items")
                
                embed.add_field(
                    name=f"📂 {cat_name.title()}",
                    value="\n".join(items_text),
                    inline=False
                )
            
            embed.add_field(
                name="💡 How to Buy",
                value=f"Use `{ctx.prefix}buy <item name>` to purchase items",
                inline=False
            )
            
            embed.set_footer(text="All items crafted with Victorian elegance 🌹")
            
            await ctx.send(embed=embed)
    
    async def buy_item(self, ctx, item_name):
        """Buy an item from the shop."""
        with self.bot.app_context:
            # Find the item
            item = ShopItem.query.filter(
                ShopItem.guild_id == str(ctx.guild.id),
                ShopItem.name.ilike(f"%{item_name}%"),
                ShopItem.purchasable == True
            ).first()
            
            if not item:
                embed = discord.Embed(
                    title="❌ Item Not Found",
                    description=f"No item found matching '{item_name}' in the shop.",
                    color=0x711417
                )
                embed.set_footer(text="Check the shop for available items 🌹")
                await ctx.send(embed=embed)
                return
            
            # Check stock
            if item.stock == 0:
                embed = discord.Embed(
                    title="📦 Out of Stock",
                    description=f"**{item.name}** is currently out of stock.",
                    color=0x711417
                )
                embed.set_footer(text="Check back later for restocks 🌹")
                await ctx.send(embed=embed)
                return
            
            # Get member data
            member_data = Member.query.filter_by(
                user_id=str(ctx.author.id),
                guild_id=str(ctx.guild.id)
            ).first()
            
            if not member_data:
                member_data = Member(
                    user_id=str(ctx.author.id),
                    guild_id=str(ctx.guild.id),
                    username=ctx.author.display_name
                )
                db.session.add(member_data)
                db.session.commit()
            
            # Check if user has enough currency
            if member_data.balance < item.price:
                guild_config = Guild.query.filter_by(guild_id=str(ctx.guild.id)).first()
                currency_name = guild_config.currency_name if guild_config else "Roses"
                
                embed = discord.Embed(
                    title="💸 Insufficient Funds",
                    description=f"You need {item.price:,} {currency_name} but only have {member_data.balance:,}.",
                    color=0x711417
                )
                embed.add_field(
                    name="💡 Earn More",
                    value="Use daily check-in and participate in activities to earn more currency!",
                    inline=False
                )
                embed.set_footer(text="The manor's treasures require dedication 🌹")
                await ctx.send(embed=embed)
                return
            
            # Process purchase
            member_data.balance -= item.price
            
            # Update stock
            if item.stock > 0:
                item.stock -= 1
            
            # Create purchase record
            purchase = Purchase(
                guild_id=str(ctx.guild.id),
                user_id=str(ctx.author.id),
                item_id=item.id,
                quantity=1,
                total_cost=item.price
            )
            db.session.add(purchase)
            
            # Give role reward if applicable
            role_message = ""
            if item.role_reward:
                try:
                    role = ctx.guild.get_role(int(item.role_reward))
                    if role and role not in ctx.author.roles:
                        await ctx.author.add_roles(role, reason=f"Purchased {item.name}")
                        role_message = f"\n🎭 You have been granted the **{role.name}** role!"
                except (ValueError, discord.Forbidden):
                    pass
            
            db.session.commit()
            
            # Get currency info
            guild_config = Guild.query.filter_by(guild_id=str(ctx.guild.id)).first()
            currency_name = guild_config.currency_name if guild_config else "Roses"
            currency_symbol = guild_config.currency_symbol if guild_config else "🌹"
            
            # Create confirmation embed
            embed = discord.Embed(
                title="🛍️ Purchase Successful!",
                description=f"You have purchased **{item.name}**!",
                color=0x711417
            )
            
            if item.description:
                embed.add_field(
                    name="📝 Description",
                    value=item.description,
                    inline=False
                )
            
            embed.add_field(
                name="💰 Cost",
                value=f"{item.price:,} {currency_symbol}",
                inline=True
            )
            
            embed.add_field(
                name="💳 New Balance",
                value=f"{member_data.balance:,} {currency_name}",
                inline=True
            )
            
            if role_message:
                embed.add_field(
                    name="🎁 Bonus",
                    value=role_message.strip(),
                    inline=False
                )
            
            embed.set_footer(text="Thank you for your patronage 🌹")
            
            await ctx.send(embed=embed)
    
    async def add_currency(self, user_id, guild_id, amount, reason="Unknown"):
        """Add currency to a user's balance."""
        with self.bot.app_context:
            member_data = Member.query.filter_by(
                user_id=str(user_id),
                guild_id=str(guild_id)
            ).first()
            
            if not member_data:
                # This should not happen in normal operation
                return False
            
            member_data.balance += amount
            db.session.commit()
            
            logger.info(f"Added {amount} currency to user {user_id} in guild {guild_id}. Reason: {reason}")
            return True
    
    async def remove_currency(self, user_id, guild_id, amount, reason="Unknown"):
        """Remove currency from a user's balance."""
        with self.bot.app_context:
            member_data = Member.query.filter_by(
                user_id=str(user_id),
                guild_id=str(guild_id)
            ).first()
            
            if not member_data or member_data.balance < amount:
                return False
            
            member_data.balance -= amount
            db.session.commit()
            
            logger.info(f"Removed {amount} currency from user {user_id} in guild {guild_id}. Reason: {reason}")
            return True
    
    async def get_leaderboard(self, guild_id, limit=10):
        """Get currency leaderboard for a guild."""
        with self.bot.app_context:
            return (Member.query.filter_by(guild_id=str(guild_id))
                    .order_by(Member.balance.desc())
                    .limit(limit).all())
