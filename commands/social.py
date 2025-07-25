import discord
from discord.ext import commands
from datetime import datetime
import config

class SocialCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='addmonitor', aliases=['monitor'])
    @commands.has_permissions(manage_guild=True)
    async def add_social_monitor(self, ctx, platform=None, username=None, channel: discord.TextChannel = None):
        """Add a social media monitor"""
        if not platform or not username:
            embed = await self.bot.create_embed(
                "📱 Social Media Monitoring",
                "Monitor social media accounts for new posts in our Gothic manor."
            )
            embed.add_field(
                name="📋 Supported Platforms",
                value="• `twitter` - Twitter/X monitoring\n• `youtube` - YouTube channel monitoring\n• `instagram` - Instagram monitoring\n• `tiktok` - TikTok monitoring",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}addmonitor <platform> <username> [#channel]`",
                inline=False
            )
            embed.add_field(
                name="Example",
                value=f"`{ctx.prefix}addmonitor twitter gothicmanor #announcements`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        platform = platform.lower()
        valid_platforms = ['twitter', 'youtube', 'instagram', 'tiktok', 'twitch']
        
        if platform not in valid_platforms:
            embed = await self.bot.create_embed(
                "Invalid Platform",
                f"Platform must be one of: {', '.join(valid_platforms)}"
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        target_channel = channel or ctx.channel
        
        # Check if monitor already exists
        existing = await self.bot.db_service.get_social_monitor(ctx.guild.id, platform, username)
        if existing:
            embed = await self.bot.create_embed(
                "Monitor Already Exists",
                f"A monitor for **{username}** on **{platform}** already exists."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Create monitor
        monitor = await self.bot.social_monitor.add_monitor(
            ctx.guild.id, platform, username, target_channel.id
        )
        
        if monitor:
            embed = await self.bot.create_embed(
                "📱 Social Monitor Added",
                f"Successfully added monitoring for **{username}** on **{platform.title()}**!"
            )
            embed.add_field(
                name="Platform",
                value=platform.title(),
                inline=True
            )
            embed.add_field(
                name="Username",
                value=username,
                inline=True
            )
            embed.add_field(
                name="Channel",
                value=target_channel.mention,
                inline=True
            )
            embed.add_field(
                name="💡 Note",
                value="New posts will be automatically announced in the specified channel with Gothic elegance.",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'social_monitor_add', {
                'platform': platform,
                'username': username,
                'channel': str(target_channel.id)
            })
        else:
            embed = await self.bot.create_embed(
                "Monitor Creation Failed",
                "Failed to create the social media monitor. Please try again."
            )
            await ctx.send(embed=embed, delete_after=10)
    
    @commands.command(name='removemonitor', aliases=['unmonitor'])
    @commands.has_permissions(manage_guild=True)
    async def remove_social_monitor(self, ctx, platform=None, username=None):
        """Remove a social media monitor"""
        if not platform or not username:
            embed = await self.bot.create_embed(
                "Remove Social Monitor",
                "Remove monitoring for a social media account."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}removemonitor <platform> <username>`",
                inline=False
            )
            embed.add_field(
                name="Example",
                value=f"`{ctx.prefix}removemonitor twitter gothicmanor`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        platform = platform.lower()
        
        # Find and remove monitor
        success = await self.bot.social_monitor.remove_monitor(ctx.guild.id, platform, username)
        
        if success:
            embed = await self.bot.create_embed(
                "📱 Monitor Removed",
                f"Successfully removed monitoring for **{username}** on **{platform.title()}**."
            )
            
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'social_monitor_remove', {
                'platform': platform,
                'username': username
            })
        else:
            embed = await self.bot.create_embed(
                "Monitor Not Found",
                f"No monitor found for **{username}** on **{platform}**."
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='monitors', aliases=['listmonitors'])
    @commands.has_permissions(manage_guild=True)
    async def list_monitors(self, ctx):
        """List all social media monitors"""
        monitors = await self.bot.social_monitor.get_guild_monitors(ctx.guild.id)
        
        if not monitors:
            embed = await self.bot.create_embed(
                "📱 No Social Monitors",
                "No social media monitors are currently active in this Gothic manor."
            )
            embed.add_field(
                name="Getting Started",
                value=f"Use `{ctx.prefix}addmonitor` to start monitoring social media accounts.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            "📱 Active Social Media Monitors",
            f"Currently monitoring {len(monitors)} social media accounts."
        )
        
        # Group by platform
        platforms = {}
        for monitor in monitors:
            if monitor.platform not in platforms:
                platforms[monitor.platform] = []
            platforms[monitor.platform].append(monitor)
        
        for platform, platform_monitors in platforms.items():
            monitor_list = []
            for monitor in platform_monitors:
                channel = ctx.guild.get_channel(int(monitor.channel_id))
                channel_mention = channel.mention if channel else "Unknown Channel"
                status_emoji = "✅" if monitor.enabled else "❌"
                
                monitor_list.append(f"{status_emoji} **{monitor.username}** → {channel_mention}")
            
            embed.add_field(
                name=f"📺 {platform.title()}",
                value="\n".join(monitor_list[:5]),  # Show first 5
                inline=False
            )
        
        embed.add_field(
            name="🔧 Management",
            value=f"Use `{ctx.prefix}removemonitor` to remove monitors",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='checkposts')
    @commands.has_permissions(manage_guild=True)
    async def manual_check(self, ctx):
        """Manually check for new social media posts"""
        embed = await self.bot.create_embed(
            "🔍 Checking Social Media",
            "Scanning the digital realm for new Gothic content..."
        )
        message = await ctx.send(embed=embed)
        
        try:
            # Run social media check
            results = await self.bot.social_monitor.check_all_monitors(ctx.guild.id)
            
            if results:
                result_embed = await self.bot.create_embed(
                    "📱 Social Media Check Complete",
                    f"Found and posted {len(results)} new updates!"
                )
                
                for platform, count in results.items():
                    result_embed.add_field(
                        name=f"📺 {platform.title()}",
                        value=f"{count} new posts",
                        inline=True
                    )
            else:
                result_embed = await self.bot.create_embed(
                    "📱 Social Media Check Complete",
                    "No new posts found at this time. The digital realm remains quiet."
                )
            
            await message.edit(embed=result_embed)
            
        except Exception as e:
            error_embed = await self.bot.create_embed(
                "Social Media Check Failed",
                "An error occurred while checking social media accounts."
            )
            await message.edit(embed=error_embed)
            print(f"Manual social check error: {e}")
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'social_manual_check', {})
    
    @commands.command(name='togglemonitor')
    @commands.has_permissions(manage_guild=True)
    async def toggle_monitor(self, ctx, platform=None, username=None):
        """Enable or disable a social media monitor"""
        if not platform or not username:
            embed = await self.bot.create_embed(
                "Toggle Social Monitor",
                "Enable or disable monitoring for a social media account."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}togglemonitor <platform> <username>`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        platform = platform.lower()
        
        # Toggle monitor status
        new_status = await self.bot.social_monitor.toggle_monitor(ctx.guild.id, platform, username)
        
        if new_status is not None:
            status_text = "enabled" if new_status else "disabled"
            emoji = "✅" if new_status else "❌"
            
            embed = await self.bot.create_embed(
                f"📱 Monitor {status_text.title()}",
                f"{emoji} Monitor for **{username}** on **{platform.title()}** has been {status_text}."
            )
            
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'social_monitor_toggle', {
                'platform': platform,
                'username': username,
                'enabled': new_status
            })
        else:
            embed = await self.bot.create_embed(
                "Monitor Not Found",
                f"No monitor found for **{username}** on **{platform}**."
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='socialstats')
    async def social_statistics(self, ctx):
        """Show social media monitoring statistics"""
        stats = await self.bot.social_monitor.get_stats(ctx.guild.id)
        
        embed = await self.bot.create_embed(
            "📊 Social Media Statistics",
            "Overview of social media monitoring in our Gothic manor"
        )
        
        embed.add_field(
            name="📱 Total Monitors",
            value=str(stats.get('total_monitors', 0)),
            inline=True
        )
        embed.add_field(
            name="✅ Active Monitors",
            value=str(stats.get('active_monitors', 0)),
            inline=True
        )
        embed.add_field(
            name="📺 Platforms",
            value=str(stats.get('platforms', 0)),
            inline=True
        )
        
        # Platform breakdown
        if stats.get('platform_breakdown'):
            platform_text = []
            for platform, count in stats['platform_breakdown'].items():
                platform_text.append(f"**{platform.title()}:** {count}")
            
            embed.add_field(
                name="📊 Platform Breakdown",
                value="\n".join(platform_text),
                inline=False
            )
        
        # Recent activity
        if stats.get('recent_posts'):
            embed.add_field(
                name="📈 Posts Last 24h",
                value=str(stats['recent_posts']),
                inline=True
            )
        
        embed.add_field(
            name="🔧 Management",
            value=f"Use `{ctx.prefix}monitors` to view all monitors",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='testpost')
    @commands.has_permissions(administrator=True)
    async def test_social_post(self, ctx, platform=None):
        """Test social media post formatting"""
        if not platform:
            embed = await self.bot.create_embed(
                "Test Social Post",
                "Test the formatting of social media post announcements."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}testpost <platform>`",
                inline=False
            )
            embed.add_field(
                name="Platforms",
                value="twitter, youtube, instagram, tiktok, twitch",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        platform = platform.lower()
        
        # Create test post data
        test_data = {
            'twitter': {
                'username': 'TestAccount',
                'content': 'Just posted some amazing Gothic content! Check it out in our Victorian manor. #Gothic #Victorian',
                'url': 'https://twitter.com/testaccount/status/123456789',
                'timestamp': datetime.utcnow()
            },
            'youtube': {
                'username': 'TestChannel',
                'title': 'Gothic Architecture: A Victorian Manor Tour',
                'description': 'Join us for an exclusive tour of a stunning Victorian Gothic manor...',
                'url': 'https://youtube.com/watch?v=testVideo123',
                'timestamp': datetime.utcnow()
            },
            'instagram': {
                'username': 'test_gothic',
                'caption': 'Captured this beautiful Gothic rose in moonlight 🌹🌙 #Gothic #Photography',
                'url': 'https://instagram.com/p/testPost123',
                'timestamp': datetime.utcnow()
            }
        }
        
        if platform not in test_data:
            embed = await self.bot.create_embed(
                "Invalid Platform",
                f"Platform '{platform}' is not supported for testing."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Format test post
        post_embed = await self.bot.social_monitor.format_post(platform, test_data[platform])
        post_embed.title = f"🧪 TEST POST - {post_embed.title}"
        post_embed.add_field(
            name="⚠️ Test Notice",
            value="This is a test post to demonstrate formatting. No actual social media content was posted.",
            inline=False
        )
        
        await ctx.send(embed=post_embed)

def setup(bot):
    bot.add_cog(SocialCommands(bot))
