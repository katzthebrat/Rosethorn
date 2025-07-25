import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from models import SocialMonitor
from main import db
import config
import logging
import discord

logger = logging.getLogger(__name__)

class SocialMonitorService:
    """Social media monitoring service"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def add_monitor(self, guild_id, platform, username, channel_id):
        """Add a new social media monitor"""
        try:
            monitor = SocialMonitor(
                guild_id=str(guild_id),
                platform=platform.lower(),
                username=username,
                channel_id=str(channel_id)
            )
            db.session.add(monitor)
            db.session.commit()
            
            await self.db_service.log_action(str(guild_id), None, 'social_monitor_add', {
                'platform': platform,
                'username': username,
                'channel_id': str(channel_id)
            })
            
            return monitor
        except Exception as e:
            logger.error(f"Error adding social monitor: {e}")
            db.session.rollback()
            return None
    
    async def remove_monitor(self, guild_id, platform, username):
        """Remove a social media monitor"""
        try:
            monitor = SocialMonitor.query.filter_by(
                guild_id=str(guild_id),
                platform=platform.lower(),
                username=username
            ).first()
            
            if monitor:
                db.session.delete(monitor)
                db.session.commit()
                
                await self.db_service.log_action(str(guild_id), None, 'social_monitor_remove', {
                    'platform': platform,
                    'username': username
                })
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing social monitor: {e}")
            db.session.rollback()
            return False
    
    async def get_guild_monitors(self, guild_id):
        """Get all monitors for a guild"""
        try:
            return SocialMonitor.query.filter_by(
                guild_id=str(guild_id),
                enabled=True
            ).all()
        except Exception as e:
            logger.error(f"Error getting guild monitors: {e}")
            return []
    
    async def toggle_monitor(self, guild_id, platform, username):
        """Toggle monitor enabled status"""
        try:
            monitor = SocialMonitor.query.filter_by(
                guild_id=str(guild_id),
                platform=platform.lower(),
                username=username
            ).first()
            
            if monitor:
                monitor.enabled = not monitor.enabled
                db.session.commit()
                return monitor.enabled
            return None
        except Exception as e:
            logger.error(f"Error toggling monitor: {e}")
            db.session.rollback()
            return None
    
    async def check_all_monitors(self, guild_id=None):
        """Check all monitors for new posts"""
        try:
            query = SocialMonitor.query.filter_by(enabled=True)
            if guild_id:
                query = query.filter_by(guild_id=str(guild_id))
            
            monitors = query.all()
            results = {}
            
            for monitor in monitors:
                try:
                    new_posts = await self.check_monitor(monitor)
                    if new_posts:
                        platform = monitor.platform
                        if platform not in results:
                            results[platform] = 0
                        results[platform] += len(new_posts)
                except Exception as e:
                    logger.error(f"Error checking monitor {monitor.id}: {e}")
            
            return results
        except Exception as e:
            logger.error(f"Error checking all monitors: {e}")
            return {}
    
    async def check_monitor(self, monitor):
        """Check a specific monitor for new posts"""
        platform = monitor.platform.lower()
        
        if platform == 'twitter':
            return await self.check_twitter(monitor)
        elif platform == 'youtube':
            return await self.check_youtube(monitor)
        elif platform == 'instagram':
            return await self.check_instagram(monitor)
        elif platform == 'tiktok':
            return await self.check_tiktok(monitor)
        elif platform == 'twitch':
            return await self.check_twitch(monitor)
        
        return []
    
    async def check_twitter(self, monitor):
        """Check Twitter for new posts"""
        if not config.TWITTER_BEARER_TOKEN:
            return []
        
        try:
            session = await self.get_session()
            headers = {
                'Authorization': f'Bearer {config.TWITTER_BEARER_TOKEN}',
                'User-Agent': 'RosethornBot/2.0'
            }
            
            # Twitter API v2 endpoint
            url = f'https://api.twitter.com/2/users/by/username/{monitor.username}'
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"Twitter API error for {monitor.username}: {response.status}")
                    return []
                
                user_data = await response.json()
                user_id = user_data['data']['id']
                
                # Get recent tweets
                tweets_url = f'https://api.twitter.com/2/users/{user_id}/tweets'
                params = {
                    'max_results': 10,
                    'tweet.fields': 'created_at,public_metrics',
                    'expansions': 'author_id'
                }
                
                if monitor.last_post_id:
                    params['since_id'] = monitor.last_post_id
                
                async with session.get(tweets_url, headers=headers, params=params) as tweets_response:
                    if tweets_response.status != 200:
                        return []
                    
                    tweets_data = await tweets_response.json()
                    
                    if 'data' not in tweets_data:
                        return []
                    
                    new_posts = []
                    latest_id = monitor.last_post_id
                    
                    for tweet in reversed(tweets_data['data']):  # Process oldest first
                        if not monitor.last_post_id or tweet['id'] > monitor.last_post_id:
                            post_data = {
                                'id': tweet['id'],
                                'content': tweet['text'],
                                'url': f"https://twitter.com/{monitor.username}/status/{tweet['id']}",
                                'timestamp': datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                                'platform': 'twitter',
                                'username': monitor.username
                            }
                            new_posts.append(post_data)
                            latest_id = tweet['id']
                    
                    # Update last post ID
                    if latest_id and latest_id != monitor.last_post_id:
                        monitor.last_post_id = latest_id
                        db.session.commit()
                    
                    # Post to Discord
                    for post in new_posts:
                        await self.post_to_discord(monitor, post)
                    
                    return new_posts
                    
        except Exception as e:
            logger.error(f"Error checking Twitter for {monitor.username}: {e}")
            return []
    
    async def check_youtube(self, monitor):
        """Check YouTube for new videos"""
        if not config.YOUTUBE_API_KEY:
            return []
        
        try:
            session = await self.get_session()
            
            # Get channel ID from username
            search_url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'part': 'snippet',
                'q': monitor.username,
                'type': 'channel',
                'key': config.YOUTUBE_API_KEY,
                'maxResults': 1
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return []
                
                search_data = await response.json()
                if not search_data.get('items'):
                    return []
                
                channel_id = search_data['items'][0]['id']['channelId']
                
                # Get recent videos
                videos_url = 'https://www.googleapis.com/youtube/v3/search'
                video_params = {
                    'part': 'snippet',
                    'channelId': channel_id,
                    'type': 'video',
                    'order': 'date',
                    'maxResults': 10,
                    'key': config.YOUTUBE_API_KEY
                }
                
                async with session.get(videos_url, params=video_params) as videos_response:
                    if videos_response.status != 200:
                        return []
                    
                    videos_data = await videos_response.json()
                    new_posts = []
                    latest_id = monitor.last_post_id
                    
                    for video in reversed(videos_data.get('items', [])):
                        video_id = video['id']['videoId']
                        if not monitor.last_post_id or video_id != monitor.last_post_id:
                            post_data = {
                                'id': video_id,
                                'title': video['snippet']['title'],
                                'description': video['snippet']['description'][:200] + '...',
                                'url': f"https://youtube.com/watch?v={video_id}",
                                'timestamp': datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00')),
                                'platform': 'youtube',
                                'username': monitor.username,
                                'thumbnail': video['snippet']['thumbnails']['medium']['url']
                            }
                            new_posts.append(post_data)
                            latest_id = video_id
                    
                    # Update last post ID
                    if latest_id and latest_id != monitor.last_post_id:
                        monitor.last_post_id = latest_id
                        db.session.commit()
                    
                    # Post to Discord
                    for post in new_posts:
                        await self.post_to_discord(monitor, post)
                    
                    return new_posts
                    
        except Exception as e:
            logger.error(f"Error checking YouTube for {monitor.username}: {e}")
            return []
    
    async def check_instagram(self, monitor):
        """Check Instagram for new posts"""
        # Instagram API requires business accounts and app review
        # For now, return empty list
        logger.info(f"Instagram monitoring for {monitor.username} - API integration pending")
        return []
    
    async def check_tiktok(self, monitor):
        """Check TikTok for new posts"""
        # TikTok API has limited access
        # For now, return empty list
        logger.info(f"TikTok monitoring for {monitor.username} - API integration pending")
        return []
    
    async def check_twitch(self, monitor):
        """Check Twitch for new streams/videos"""
        # Twitch API integration would go here
        logger.info(f"Twitch monitoring for {monitor.username} - API integration pending")
        return []
    
    async def post_to_discord(self, monitor, post_data):
        """Post social media update to Discord"""
        try:
            from bot import RosethornBot
            
            # This would need the bot instance
            # For now, we'll just log the post
            logger.info(f"New {post_data['platform']} post from {post_data['username']}: {post_data.get('content', post_data.get('title', 'New post'))}")
            
            # In a real implementation, you'd send to the Discord channel
            # embed = await self.format_post(post_data['platform'], post_data)
            # channel = bot.get_channel(int(monitor.channel_id))
            # if channel:
            #     await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error posting to Discord: {e}")
    
    async def format_post(self, platform, post_data):
        """Format social media post as Discord embed"""
        embed = discord.Embed(
            title=f"📱 New {platform.title()} Post",
            color=config.EMBED_COLOR,
            timestamp=post_data['timestamp']
        )
        
        if platform == 'twitter':
            embed.description = post_data['content'][:2000]
            embed.add_field(
                name="🐦 Twitter",
                value=f"[@{post_data['username']}]({post_data['url']})",
                inline=True
            )
        elif platform == 'youtube':
            embed.title = post_data['title']
            embed.description = post_data['description']
            embed.add_field(
                name="📺 YouTube",
                value=f"[{post_data['username']}]({post_data['url']})",
                inline=True
            )
            if 'thumbnail' in post_data:
                embed.set_image(url=post_data['thumbnail'])
        
        embed.add_field(
            name="🔗 Link",
            value=f"[View Post]({post_data['url']})",
            inline=True
        )
        
        embed.set_footer(text="🌹 Social Media Monitor - Gothic Excellence")
        
        return embed
    
    async def get_stats(self, guild_id):
        """Get social monitoring statistics"""
        try:
            total_monitors = SocialMonitor.query.filter_by(guild_id=str(guild_id)).count()
            active_monitors = SocialMonitor.query.filter_by(
                guild_id=str(guild_id),
                enabled=True
            ).count()
            
            # Platform breakdown
            platforms = db.session.query(
                SocialMonitor.platform,
                db.func.count(SocialMonitor.id).label('count')
            ).filter_by(guild_id=str(guild_id)).group_by(SocialMonitor.platform).all()
            
            platform_breakdown = {platform: count for platform, count in platforms}
            
            return {
                'total_monitors': total_monitors,
                'active_monitors': active_monitors,
                'platforms': len(platform_breakdown),
                'platform_breakdown': platform_breakdown,
                'recent_posts': 0  # Would track recent posts in real implementation
            }
        except Exception as e:
            logger.error(f"Error getting social stats: {e}")
            return {}
    
    async def get_social_monitor(self, guild_id, platform, username):
        """Get specific social monitor"""
        try:
            return SocialMonitor.query.filter_by(
                guild_id=str(guild_id),
                platform=platform.lower(),
                username=username
            ).first()
        except Exception as e:
            logger.error(f"Error getting social monitor: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
