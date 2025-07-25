import os
import asyncio
import aiohttp
import discord
from datetime import datetime, timedelta
from main import db
from models import SocialMediaConfig, BotLog, Guild
import logging
import json

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Social media monitoring and cross-platform integration."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # API credentials from environment
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY', '')
        self.twitch_client_id = os.getenv('TWITCH_CLIENT_ID', '')
        self.twitch_client_secret = os.getenv('TWITCH_CLIENT_SECRET', '')
        
        # Session for HTTP requests
        self.session = None
        
        # Cache for API tokens
        self.twitch_token = None
        self.twitch_token_expires = None
    
    async def initialize(self):
        """Initialize the social media service."""
        self.session = aiohttp.ClientSession()
        await self.refresh_twitch_token()
        logger.info("🌹 Social Media Service initialized")
    
    async def close(self):
        """Close the service and cleanup resources."""
        if self.session:
            await self.session.close()
    
    async def refresh_twitch_token(self):
        """Refresh Twitch API token."""
        if not self.twitch_client_id or not self.twitch_client_secret:
            return
        
        try:
            data = {
                'client_id': self.twitch_client_id,
                'client_secret': self.twitch_client_secret,
                'grant_type': 'client_credentials'
            }
            
            async with self.session.post('https://id.twitch.tv/oauth2/token', data=data) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    self.twitch_token = token_data.get('access_token')
                    expires_in = token_data.get('expires_in', 3600)
                    self.twitch_token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                    logger.info("🟣 Twitch API token refreshed")
        except Exception as e:
            logger.error(f"Failed to refresh Twitch token: {e}")
    
    async def check_twitter_updates(self, config):
        """Check for new Twitter/X posts."""
        if not self.twitter_bearer_token:
            return
        
        try:
            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}',
                'User-Agent': 'RosethornBot/1.0'
            }
            
            # Get user timeline
            url = f'https://api.twitter.com/2/users/by/username/{config.username}/tweets'
            params = {
                'max_results': 5,
                'tweet.fields': 'created_at,public_metrics,context_annotations',
                'expansions': 'author_id'
            }
            
            if config.last_post_id:
                params['since_id'] = config.last_post_id
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tweets = data.get('data', [])
                    
                    if tweets:
                        # Process new tweets
                        for tweet in reversed(tweets):  # Process oldest first
                            await self.announce_twitter_post(config, tweet)
                        
                        # Update last post ID
                        with self.bot.app_context:
                            config.last_post_id = tweets[0]['id']
                            db.session.commit()
                
                elif resp.status == 429:
                    logger.warning("Twitter API rate limit exceeded")
                else:
                    logger.warning(f"Twitter API error: {resp.status}")
        
        except Exception as e:
            logger.error(f"Error checking Twitter updates for {config.username}: {e}")
    
    async def announce_twitter_post(self, config, tweet):
        """Announce a new Twitter post in Discord."""
        try:
            guild = self.bot.get_guild(int(config.guild_id))
            if not guild:
                return
            
            channel = guild.get_channel(int(config.announcement_channel))
            if not channel:
                return
            
            # Create embed
            embed = discord.Embed(
                title="🐦 New Tweet",
                description=tweet['text'][:2000],  # Discord limit
                color=0x711417,
                url=f"https://twitter.com/{config.username}/status/{tweet['id']}",
                timestamp=datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
            )
            
            embed.set_author(
                name=f"@{config.username}",
                icon_url="https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
            )
            
            # Add metrics if available
            metrics = tweet.get('public_metrics', {})
            if metrics:
                embed.add_field(
                    name="📊 Engagement",
                    value=f"❤️ {metrics.get('like_count', 0)} | "
                          f"🔄 {metrics.get('retweet_count', 0)} | "
                          f"💬 {metrics.get('reply_count', 0)}",
                    inline=False
                )
            
            embed.set_footer(text="Posted on Twitter/X 🌹")
            
            await channel.send(embed=embed)
            
            # Log the announcement
            await self.log_social_media_event(
                guild_id=config.guild_id,
                platform="twitter",
                username=config.username,
                action="announced_post",
                post_id=tweet['id']
            )
        
        except Exception as e:
            logger.error(f"Error announcing Twitter post: {e}")
    
    async def check_youtube_updates(self, config):
        """Check for new YouTube videos."""
        if not self.youtube_api_key:
            return
        
        try:
            # Get channel ID first
            url = 'https://www.googleapis.com/youtube/v3/channels'
            params = {
                'key': self.youtube_api_key,
                'forUsername': config.username,
                'part': 'id'
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    channels = data.get('items', [])
                    
                    if not channels:
                        # Try by channel handle
                        params['forHandle'] = f"@{config.username}"
                        del params['forUsername']
                        
                        async with self.session.get(url, params=params) as resp2:
                            if resp2.status == 200:
                                data = await resp2.json()
                                channels = data.get('items', [])
                    
                    if channels:
                        channel_id = channels[0]['id']
                        await self.check_youtube_channel_videos(config, channel_id)
        
        except Exception as e:
            logger.error(f"Error checking YouTube updates for {config.username}: {e}")
    
    async def check_youtube_channel_videos(self, config, channel_id):
        """Check for new videos from a YouTube channel."""
        try:
            url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'key': self.youtube_api_key,
                'channelId': channel_id,
                'part': 'snippet',
                'order': 'date',
                'maxResults': 5,
                'type': 'video'
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    videos = data.get('items', [])
                    
                    for video in reversed(videos):  # Process oldest first
                        video_id = video['id']['videoId']
                        
                        # Check if this is a new video
                        if config.last_post_id and video_id <= config.last_post_id:
                            continue
                        
                        await self.announce_youtube_video(config, video)
                    
                    if videos:
                        # Update last post ID
                        with self.bot.app_context:
                            config.last_post_id = videos[0]['id']['videoId']
                            db.session.commit()
        
        except Exception as e:
            logger.error(f"Error checking YouTube channel videos: {e}")
    
    async def announce_youtube_video(self, config, video):
        """Announce a new YouTube video in Discord."""
        try:
            guild = self.bot.get_guild(int(config.guild_id))
            if not guild:
                return
            
            channel = guild.get_channel(int(config.announcement_channel))
            if not channel:
                return
            
            video_id = video['id']['videoId']
            snippet = video['snippet']
            
            # Create embed
            embed = discord.Embed(
                title="📺 New YouTube Video",
                description=snippet['title'],
                color=0x711417,
                url=f"https://www.youtube.com/watch?v={video_id}",
                timestamp=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
            )
            
            embed.set_author(
                name=snippet['channelTitle'],
                icon_url="https://www.youtube.com/s/desktop/12345678/img/favicon_144x144.png"
            )
            
            # Add thumbnail
            thumbnail = snippet.get('thumbnails', {}).get('high', {}).get('url')
            if thumbnail:
                embed.set_image(url=thumbnail)
            
            # Add description if available
            description = snippet.get('description', '')
            if description:
                embed.add_field(
                    name="📝 Description",
                    value=description[:500] + ("..." if len(description) > 500 else ""),
                    inline=False
                )
            
            embed.set_footer(text="New video on YouTube 🌹")
            
            await channel.send(embed=embed)
            
            # Log the announcement
            await self.log_social_media_event(
                guild_id=config.guild_id,
                platform="youtube",
                username=config.username,
                action="announced_video",
                post_id=video_id
            )
        
        except Exception as e:
            logger.error(f"Error announcing YouTube video: {e}")
    
    async def check_twitch_updates(self, config):
        """Check for Twitch stream updates."""
        if not self.twitch_token or not self.twitch_client_id:
            return
        
        # Refresh token if needed
        if self.twitch_token_expires and datetime.utcnow() >= self.twitch_token_expires:
            await self.refresh_twitch_token()
        
        try:
            headers = {
                'Client-ID': self.twitch_client_id,
                'Authorization': f'Bearer {self.twitch_token}'
            }
            
            # Get user info first
            url = 'https://api.twitch.tv/helix/users'
            params = {'login': config.username}
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    users = data.get('data', [])
                    
                    if users:
                        user_id = users[0]['id']
                        await self.check_twitch_stream(config, user_id, headers)
        
        except Exception as e:
            logger.error(f"Error checking Twitch updates for {config.username}: {e}")
    
    async def check_twitch_stream(self, config, user_id, headers):
        """Check if a Twitch user is streaming."""
        try:
            url = 'https://api.twitch.tv/helix/streams'
            params = {'user_id': user_id}
            
            async with self.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    streams = data.get('data', [])
                    
                    if streams:
                        stream = streams[0]
                        stream_id = stream['id']
                        
                        # Check if this is a new stream
                        if config.last_post_id == stream_id:
                            return
                        
                        await self.announce_twitch_stream(config, stream)
                        
                        # Update last post ID
                        with self.bot.app_context:
                            config.last_post_id = stream_id
                            db.session.commit()
        
        except Exception as e:
            logger.error(f"Error checking Twitch stream: {e}")
    
    async def announce_twitch_stream(self, config, stream):
        """Announce a Twitch stream going live."""
        try:
            guild = self.bot.get_guild(int(config.guild_id))
            if not guild:
                return
            
            channel = guild.get_channel(int(config.announcement_channel))
            if not channel:
                return
            
            # Create embed
            embed = discord.Embed(
                title="🔴 LIVE on Twitch!",
                description=stream['title'],
                color=0x711417,
                url=f"https://www.twitch.tv/{config.username}",
                timestamp=datetime.fromisoformat(stream['started_at'].replace('Z', '+00:00'))
            )
            
            embed.set_author(
                name=stream['user_name'],
                icon_url="https://static.twitchcdn.net/assets/favicon-32-d6025c14e900565d6177.png"
            )
            
            # Add game/category
            if stream.get('game_name'):
                embed.add_field(
                    name="🎮 Playing",
                    value=stream['game_name'],
                    inline=True
                )
            
            # Add viewer count
            embed.add_field(
                name="👀 Viewers",
                value=f"{stream['viewer_count']:,}",
                inline=True
            )
            
            # Add thumbnail
            thumbnail_url = stream['thumbnail_url'].replace('{width}', '640').replace('{height}', '360')
            embed.set_image(url=thumbnail_url)
            
            embed.set_footer(text="Now streaming on Twitch 🌹")
            
            await channel.send(embed=embed)
            
            # Log the announcement
            await self.log_social_media_event(
                guild_id=config.guild_id,
                platform="twitch",
                username=config.username,
                action="announced_stream",
                post_id=stream['id']
            )
        
        except Exception as e:
            logger.error(f"Error announcing Twitch stream: {e}")
    
    async def monitor_social_media(self):
        """Main monitoring loop for all configured social media."""
        while True:
            try:
                with self.bot.app_context:
                    configs = SocialMediaConfig.query.filter_by(enabled=True).all()
                
                for config in configs:
                    try:
                        if config.platform == 'twitter':
                            await self.check_twitter_updates(config)
                        elif config.platform == 'youtube':
                            await self.check_youtube_updates(config)
                        elif config.platform == 'twitch':
                            await self.check_twitch_updates(config)
                        
                        # Small delay between checks
                        await asyncio.sleep(1)
                    
                    except Exception as e:
                        logger.error(f"Error monitoring {config.platform}/{config.username}: {e}")
                
                # Wait before next monitoring cycle (5 minutes)
                await asyncio.sleep(300)
            
            except Exception as e:
                logger.error(f"Error in social media monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def add_social_media_config(self, guild_id, platform, username, channel_id):
        """Add a new social media monitoring configuration."""
        with self.bot.app_context:
            config = SocialMediaConfig(
                guild_id=str(guild_id),
                platform=platform.lower(),
                username=username,
                announcement_channel=str(channel_id)
            )
            db.session.add(config)
            db.session.commit()
            
            logger.info(f"Added social media config: {platform}/{username} for guild {guild_id}")
            return config
    
    async def remove_social_media_config(self, guild_id, platform, username):
        """Remove a social media monitoring configuration."""
        with self.bot.app_context:
            config = SocialMediaConfig.query.filter_by(
                guild_id=str(guild_id),
                platform=platform.lower(),
                username=username
            ).first()
            
            if config:
                db.session.delete(config)
                db.session.commit()
                logger.info(f"Removed social media config: {platform}/{username} for guild {guild_id}")
                return True
            
            return False
    
    async def log_social_media_event(self, guild_id, platform, username, action, post_id=None):
        """Log social media events."""
        with self.bot.app_context:
            log_entry = BotLog(
                guild_id=guild_id,
                level="INFO",
                module="social_media",
                message=f"Social media event: {action} for {platform}/{username}",
                extra_data={
                    "platform": platform,
                    "username": username,
                    "action": action,
                    "post_id": post_id
                }
            )
            db.session.add(log_entry)
            db.session.commit()
    
    async def get_social_media_configs(self, guild_id):
        """Get all social media configurations for a guild."""
        with self.bot.app_context:
            return SocialMediaConfig.query.filter_by(guild_id=str(guild_id)).all()
