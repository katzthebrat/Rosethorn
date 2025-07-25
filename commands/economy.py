import discord
from discord.ext import commands
from datetime import datetime
import config
from utils import format_currency, get_user_level, xp_for_level

class EconomyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='balance', aliases=['bal', 'currency'])
    async def check_balance(self, ctx, member: discord.Member = None):
        """Check currency balance"""
        target = member or ctx.author
        user = await self.bot.db_service.get_or_create_user(target.id)
        
        embed = await self.bot.create_embed(
            f"Treasury of {target.display_name}",
            f"Your Gothic wealth shimmers in the candlelight..."
        )
        embed.add_field(
            name="🌹 Currency Balance",
            value=format_currency(user.currency),
            inline=True
        )
        embed.add_field(
            name="⭐ Experience Points",
            value=f"{user.xp:,} XP",
            inline=True
        )
        embed.add_field(
            name="👑 Level",
            value=f"Level {user.level}",
            inline=True
        )
        
        # Progress to next level
        current_level_xp = xp_for_level(user.level)
        next_level_xp = xp_for_level(user.level + 1)
        progress = user.xp - current_level_xp
        needed = next_level_xp - current_level_xp
        
        progress_bar = "▓" * int((progress / needed) * 10) + "░" * (10 - int((progress / needed) * 10))
        
        embed.add_field(
            name="📈 Level Progress",
            value=f"`{progress_bar}` {progress}/{needed} XP",
            inline=False
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(name='daily', aliases=['checkin'])
    async def daily_reward(self, ctx):
        """Claim daily currency reward"""
        guild_config = await self.bot.db_service.get_guild_config(ctx.guild.id)
        base_reward = guild_config.daily_reward if guild_config else 100
        
        result, error = await self.bot.economy_service.daily_reward(
            ctx.author.id, ctx.guild.id, base_reward
        )
        
        if error:
            embed = await self.bot.create_embed(
                "Daily Reward",
                f"Alas, {error.lower()}. Return tomorrow for thy Gothic bounty."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        embed = await self.bot.create_embed(
            "Daily Bounty Claimed",
            f"Thy daily tribute has been bestowed upon thee! 🌹"
        )
        embed.add_field(
            name="💰 Reward",
            value=format_currency(result['reward']),
            inline=True
        )
        embed.add_field(
            name="🔥 Streak",
            value=f"{result['streak']} days",
            inline=True
        )
        embed.add_field(
            name="🎁 Streak Bonus",
            value=format_currency(result['streak_bonus']),
            inline=True
        )
        embed.add_field(
            name="💎 New Balance",
            value=format_currency(result['new_balance']),
            inline=False
        )
        
        if result['streak'] > 1:
            embed.set_footer(text=f"🕯️ Keep thy streak alive for greater Gothic rewards!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='shop')
    async def view_shop(self, ctx, category=None):
        """View the Gothic marketplace"""
        items = await self.bot.economy_service.get_shop_items(ctx.guild.id, category)
        
        if not items:
            embed = await self.bot.create_embed(
                "Empty Marketplace",
                "The Gothic marketplace stands empty, awaiting noble wares..."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            "🏪 Gothic Marketplace",
            "Welcome to our Victorian emporium of mystical goods..."
        )
        
        for item in items[:10]:  # Show first 10 items
            stock_text = f"Stock: {item.stock}" if item.stock != -1 else "Unlimited"
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.rarity, "⚪")
            
            embed.add_field(
                name=f"{rarity_emoji} {item.name}",
                value=f"**Price:** {format_currency(item.price)}\n**{stock_text}**\n{item.description[:50]}{'...' if len(item.description) > 50 else ''}",
                inline=True
            )
        
        embed.set_footer(text=f"Use '{ctx.prefix}buy <item_name>' to purchase items")
        await ctx.send(embed=embed)
    
    @commands.command(name='buy')
    async def buy_item(self, ctx, *, item_name):
        """Purchase an item from the shop"""
        items = await self.bot.economy_service.get_shop_items(ctx.guild.id)
        
        # Find item by name (case insensitive)
        item = None
        for shop_item in items:
            if shop_item.name.lower() == item_name.lower():
                item = shop_item
                break
        
        if not item:
            embed = await self.bot.create_embed(
                "Item Not Found",
                f"The item '{item_name}' does not exist in our Gothic marketplace."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        result, error = await self.bot.economy_service.purchase_item(ctx.author.id, item.id)
        
        if error:
            embed = await self.bot.create_embed(
                "Purchase Failed",
                f"Alas, thy purchase has failed: {error}"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        embed = await self.bot.create_embed(
            "Purchase Complete",
            f"Thy acquisition of **{result['item_name']}** is complete! The Gothic treasure is now thine."
        )
        embed.add_field(
            name="💰 Cost",
            value=format_currency(result['total_cost']),
            inline=True
        )
        embed.add_field(
            name="📦 Quantity",
            value=str(result['quantity']),
            inline=True
        )
        embed.add_field(
            name="💎 Remaining Balance",
            value=format_currency(result['new_balance']),
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='inventory', aliases=['inv'])
    async def view_inventory(self, ctx, member: discord.Member = None):
        """View user's inventory"""
        target = member or ctx.author
        inventory = await self.bot.economy_service.get_user_inventory(target.id)
        
        if not inventory:
            embed = await self.bot.create_embed(
                f"Empty Chambers of {target.display_name}",
                "The inventory chambers stand empty, awaiting Gothic treasures..."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            f"🎒 Inventory of {target.display_name}",
            "Behold the collected Gothic treasures..."
        )
        
        for inv_item in inventory[:15]:  # Show first 15 items
            item = inv_item['item']
            quantity = inv_item['quantity']
            
            rarity_emoji = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.rarity, "⚪")
            
            embed.add_field(
                name=f"{rarity_emoji} {item.name}",
                value=f"**Quantity:** {quantity}\n**Value:** {format_currency(item.price * quantity)}",
                inline=True
            )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(name='gamble', aliases=['bet'])
    async def gamble_currency(self, ctx, amount: int, game: str = "coinflip"):
        """Gamble currency in various games"""
        if amount <= 0:
            embed = await self.bot.create_embed(
                "Invalid Wager",
                "Thou must wager a positive amount of Gothic currency."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        valid_games = ["coinflip", "slots", "dice"]
        if game.lower() not in valid_games:
            embed = await self.bot.create_embed(
                "Invalid Game",
                f"Valid gambling games: {', '.join(valid_games)}"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        result, error = await self.bot.economy_service.gamble(ctx.author.id, amount, game.lower())
        
        if error:
            embed = await self.bot.create_embed(
                "Gambling Failed",
                f"Thy wager has been rejected: {error}"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if result['won']:
            embed = await self.bot.create_embed(
                "🎉 Victory in the Gothic Games!",
                f"Fortune smiles upon thee! Thy {game} wager has succeeded!"
            )
            embed.color = 0x00FF00
        else:
            embed = await self.bot.create_embed(
                "💀 Defeat in the Gothic Games",
                f"The shadows have claimed thy wager... Better luck next time."
            )
            embed.color = 0xFF0000
        
        embed.add_field(
            name="🎰 Game",
            value=game.title(),
            inline=True
        )
        embed.add_field(
            name="💰 Wager",
            value=format_currency(amount),
            inline=True
        )
        embed.add_field(
            name="🏆 Winnings" if result['won'] else "💸 Lost",
            value=format_currency(result['winnings'] if result['won'] else amount),
            inline=True
        )
        embed.add_field(
            name="💎 New Balance",
            value=format_currency(result['new_balance']),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='give', aliases=['transfer'])
    async def transfer_currency(self, ctx, member: discord.Member, amount: int):
        """Transfer currency to another member"""
        if amount <= 0:
            embed = await self.bot.create_embed(
                "Invalid Amount",
                "Thou must transfer a positive amount of Gothic currency."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if member == ctx.author:
            embed = await self.bot.create_embed(
                "Self Transfer",
                "Thou cannot bestow currency upon thyself!"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        result, error = await self.bot.economy_service.transfer_currency(
            ctx.author.id, member.id, amount
        )
        
        if error:
            embed = await self.bot.create_embed(
                "Transfer Failed",
                f"Thy generous gesture has failed: {error}"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        embed = await self.bot.create_embed(
            "💝 Gothic Generosity",
            f"{ctx.author.mention} has bestowed {format_currency(amount)} upon {member.mention}!"
        )
        embed.add_field(
            name="💰 Amount",
            value=format_currency(amount),
            inline=True
        )
        embed.add_field(
            name="🎁 Recipient",
            value=member.mention,
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def currency_leaderboard(self, ctx, metric: str = "currency"):
        """View the Gothic leaderboard"""
        valid_metrics = ["currency", "xp", "level"]
        if metric.lower() not in valid_metrics:
            metric = "currency"
        
        top_users = await self.bot.db_service.get_leaderboard(ctx.guild.id, metric.lower(), 10)
        
        if not top_users:
            embed = await self.bot.create_embed(
                "Empty Leaderboard",
                "No worthy souls have yet claimed their place on the Gothic leaderboard..."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            f"🏆 Gothic Leaderboard - {metric.title()}",
            "Behold the most distinguished members of our Gothic realm..."
        )
        
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, user in enumerate(top_users):
            if metric.lower() == "currency":
                value = format_currency(user.currency)
            elif metric.lower() == "xp":
                value = f"{user.xp:,} XP"
            else:  # level
                value = f"Level {user.level}"
            
            embed.add_field(
                name=f"{emojis[i]} {user.username}",
                value=value,
                inline=True
            )
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(EconomyCommands(bot))
