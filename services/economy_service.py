import asyncio
from datetime import datetime, timedelta
from models import User, ShopItem, InventoryItem, CheckIn
from main import db
import logging

logger = logging.getLogger(__name__)

class EconomyService:
    """Economy system service"""
    
    def __init__(self, db_service):
        self.db_service = db_service
    
    async def add_currency(self, user_id, amount, reason="Unknown"):
        """Add currency to user"""
        try:
            new_balance = await self.db_service.update_user_currency(user_id, amount, 'add')
            await self.db_service.log_action('economy', user_id, 'currency_add', {
                'amount': amount,
                'reason': reason,
                'new_balance': new_balance
            })
            return new_balance
        except Exception as e:
            logger.error(f"Error adding currency: {e}")
            return None
    
    async def remove_currency(self, user_id, amount, reason="Purchase"):
        """Remove currency from user"""
        try:
            user = await self.db_service.get_or_create_user(user_id)
            if user.currency < amount:
                return None  # Insufficient funds
            
            new_balance = await self.db_service.update_user_currency(user_id, amount, 'subtract')
            await self.db_service.log_action('economy', user_id, 'currency_remove', {
                'amount': amount,
                'reason': reason,
                'new_balance': new_balance
            })
            return new_balance
        except Exception as e:
            logger.error(f"Error removing currency: {e}")
            return None
    
    async def get_user_balance(self, user_id):
        """Get user's currency balance"""
        try:
            user = await self.db_service.get_or_create_user(user_id)
            return user.currency
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
    
    async def daily_reward(self, user_id, guild_id, base_amount=100):
        """Give daily reward"""
        try:
            # Check if already claimed today
            checkin, is_new = await self.db_service.record_checkin(user_id, guild_id)
            
            if not is_new:
                return None, "Already claimed today"
            
            # Calculate reward based on streak
            streak_bonus = min(checkin.streak * 10, 500)  # Max 500 bonus
            total_reward = base_amount + streak_bonus
            
            # Add currency
            new_balance = await self.add_currency(user_id, total_reward, "Daily check-in")
            
            # Update check-in record
            checkin.reward_claimed = total_reward
            db.session.commit()
            
            return {
                'reward': total_reward,
                'streak': checkin.streak,
                'streak_bonus': streak_bonus,
                'new_balance': new_balance
            }, None
        except Exception as e:
            logger.error(f"Error with daily reward: {e}")
            return None, "System error"
    
    async def purchase_item(self, user_id, item_id, quantity=1):
        """Purchase item from shop"""
        try:
            user = await self.db_service.get_or_create_user(user_id)
            item = ShopItem.query.get(item_id)
            
            if not item or not item.enabled:
                return None, "Item not found or unavailable"
            
            total_cost = item.price * quantity
            
            if user.currency < total_cost:
                return None, "Insufficient funds"
            
            if item.stock != -1 and item.stock < quantity:
                return None, "Insufficient stock"
            
            # Remove currency
            new_balance = await self.remove_currency(user_id, total_cost, f"Purchase: {item.name}")
            
            # Add to inventory
            existing_inventory = InventoryItem.query.filter_by(
                user_id=user.id,
                item_id=item.id
            ).first()
            
            if existing_inventory:
                existing_inventory.quantity += quantity
            else:
                inventory_item = InventoryItem(
                    user_id=user.id,
                    item_id=item.id,
                    quantity=quantity
                )
                db.session.add(inventory_item)
            
            # Update stock
            if item.stock != -1:
                item.stock -= quantity
            
            db.session.commit()
            
            return {
                'item_name': item.name,
                'quantity': quantity,
                'total_cost': total_cost,
                'new_balance': new_balance
            }, None
        except Exception as e:
            logger.error(f"Error purchasing item: {e}")
            db.session.rollback()
            return None, "Purchase failed"
    
    async def get_user_inventory(self, user_id):
        """Get user's inventory"""
        try:
            user = await self.db_service.get_or_create_user(user_id)
            inventory = InventoryItem.query.filter_by(user_id=user.id).all()
            
            result = []
            for inv_item in inventory:
                result.append({
                    'item': inv_item.item,
                    'quantity': inv_item.quantity,
                    'acquired_at': inv_item.acquired_at
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting inventory: {e}")
            return []
    
    async def create_shop_item(self, guild_id, name, description, price, category="misc", rarity="common", stock=-1):
        """Create new shop item"""
        try:
            item = ShopItem(
                guild_id=str(guild_id),
                name=name,
                description=description,
                price=price,
                category=category,
                rarity=rarity,
                stock=stock
            )
            db.session.add(item)
            db.session.commit()
            return item
        except Exception as e:
            logger.error(f"Error creating shop item: {e}")
            db.session.rollback()
            return None
    
    async def get_shop_items(self, guild_id, category=None):
        """Get shop items for guild"""
        try:
            query = ShopItem.query.filter_by(guild_id=str(guild_id), enabled=True)
            
            if category:
                query = query.filter_by(category=category)
            
            return query.order_by(ShopItem.price).all()
        except Exception as e:
            logger.error(f"Error getting shop items: {e}")
            return []
    
    async def gamble(self, user_id, amount, game_type="coinflip"):
        """Gambling system"""
        try:
            import random
            
            user = await self.db_service.get_or_create_user(user_id)
            
            if user.currency < amount:
                return None, "Insufficient funds"
            
            # Remove bet amount
            await self.remove_currency(user_id, amount, f"Gambling: {game_type}")
            
            won = False
            winnings = 0
            
            if game_type == "coinflip":
                won = random.choice([True, False])
                if won:
                    winnings = amount * 2
            elif game_type == "slots":
                # Simple slots with 20% win rate
                won = random.random() < 0.2
                if won:
                    multiplier = random.choice([2, 3, 5, 10])
                    winnings = amount * multiplier
            elif game_type == "dice":
                # Roll 1-6, win on 4-6
                roll = random.randint(1, 6)
                won = roll >= 4
                if won:
                    winnings = amount * 1.5
            
            if won and winnings > 0:
                new_balance = await self.add_currency(user_id, winnings, f"Gambling win: {game_type}")
            else:
                user = await self.db_service.get_or_create_user(user_id)
                new_balance = user.currency
            
            return {
                'won': won,
                'winnings': winnings,
                'net_change': winnings - amount,
                'new_balance': new_balance,
                'game_type': game_type
            }, None
        except Exception as e:
            logger.error(f"Error with gambling: {e}")
            return None, "Gambling failed"
    
    async def transfer_currency(self, from_user_id, to_user_id, amount):
        """Transfer currency between users"""
        try:
            from_user = await self.db_service.get_or_create_user(from_user_id)
            
            if from_user.currency < amount:
                return None, "Insufficient funds"
            
            # Remove from sender
            await self.remove_currency(from_user_id, amount, "Transfer out")
            
            # Add to receiver
            await self.add_currency(to_user_id, amount, "Transfer in")
            
            return {
                'amount': amount,
                'from_user': from_user_id,
                'to_user': to_user_id
            }, None
        except Exception as e:
            logger.error(f"Error transferring currency: {e}")
            return None, "Transfer failed"
    
    async def get_economy_stats(self, guild_id):
        """Get economy statistics"""
        try:
            total_currency = db.session.query(db.func.sum(User.currency)).scalar() or 0
            total_users = User.query.count()
            total_items = ShopItem.query.filter_by(guild_id=str(guild_id)).count()
            daily_checkins = CheckIn.query.filter(
                CheckIn.date >= datetime.utcnow().date()
            ).count()
            
            return {
                'total_currency': total_currency,
                'total_users': total_users,
                'total_items': total_items,
                'daily_checkins': daily_checkins,
                'average_balance': total_currency / max(total_users, 1)
            }
        except Exception as e:
            logger.error(f"Error getting economy stats: {e}")
            return {}
