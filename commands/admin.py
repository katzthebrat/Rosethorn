import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import config

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def server_setup(self, ctx):
        """Setup the bot for this server"""
        embed = await self.bot.create_embed(
            "🏰 Gothic Manor Setup",
            "Welcome to the RosethornBot setup wizard! Let's configure thy Gothic manor."
        )
        embed.add_field(
            name="📋 Setup Process",
            value="I will guide thee through configuring channels, roles, and features for optimal Gothic elegance.",
            inline=False
        )
        
        setup_msg = await ctx.send(embed=embed)
        
        # Create or get guild config
        guild_config = await self.bot.db_service.get_guild_config(ctx.guild.id)
        if not guild_config:
            guild_config = await self.bot.db_service.create_guild_config(ctx.guild.id, ctx.guild.name)
        
        # Setup channels
        channels_created = 0
        
        # Welcome channel
        welcome_channel = discord.utils.get(ctx.guild.text_channels, name='welcome')
        if not welcome_channel:
            try:
                welcome_channel = await ctx.guild.create_text_channel(
                    'welcome',
                    topic='Welcome new members to our Gothic manor 🌹'
                )
                channels_created += 1
            except discord.Forbidden:
                pass
        
        # Mod log channel
        mod_log_channel = discord.utils.get(ctx.guild.text_channels, name='mod-log')
        if not mod_log_channel:
            try:
                mod_log_channel = await ctx.guild.create_text_channel(
                    'mod-log',
                    topic='Moderation actions and audit logs 📋'
                )
                channels_created += 1
            except discord.Forbidden:
                pass
        
        # Staff channel
        staff_channel = discord.utils.get(ctx.guild.text_channels, name='staff-chat')
        if not staff_channel:
            try:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                
                # Add admin permissions
                for role in ctx.guild.roles:
                    if role.permissions.administrator:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
                staff_channel = await ctx.guild.create_text_channel(
                    'staff-chat',
                    overwrites=overwrites,
                    topic='Private staff discussions 👑'
                )
                channels_created += 1
            except discord.Forbidden:
                pass
        
        # Ticket category
        ticket_category = discord.utils.get(ctx.guild.categories, name='🎫 Support Tickets')
        if not ticket_category:
            try:
                ticket_category = await ctx.guild.create_category('🎫 Support Tickets')
                channels_created += 1
            except discord.Forbidden:
                pass
        
        # Update guild config with channel IDs
        if welcome_channel:
            guild_config.welcome_channel = str(welcome_channel.id)
        if mod_log_channel:
            guild_config.mod_log_channel = str(mod_log_channel.id)
        if staff_channel:
            guild_config.staff_channel = str(staff_channel.id)
        if ticket_category:
            guild_config.ticket_category = str(ticket_category.id)
        
        # Save config
        from main import db
        db.session.commit()
        
        # Create roles
        roles_created = 0
        
        # Muted role
        muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(
                    name='Muted',
                    color=discord.Color.dark_grey(),
                    reason='Auto-created mute role for moderation'
                )
                
                # Set permissions for all channels
                for channel in ctx.guild.channels:
                    try:
                        await channel.set_permissions(
                            muted_role,
                            send_messages=False,
                            speak=False,
                            add_reactions=False
                        )
                    except discord.Forbidden:
                        pass
                
                roles_created += 1
            except discord.Forbidden:
                pass
        
        # Complete setup
        final_embed = await self.bot.create_embed(
            "✅ Gothic Manor Setup Complete",
            "Thy server has been configured with Victorian elegance!"
        )
        final_embed.add_field(
            name="📊 Setup Summary",
            value=f"**Channels Created:** {channels_created}\n**Roles Created:** {roles_created}",
            inline=True
        )
        final_embed.add_field(
            name="🔧 Configuration",
            value=f"**Prefix:** {guild_config.prefix}\n**Currency:** {guild_config.currency_name}",
            inline=True
        )
        final_embed.add_field(
            name="📋 Next Steps",
            value=f"• Visit the dashboard: {config.DASHBOARD_URL}\n• Use `{guild_config.prefix}help` for commands\n• Configure features with `{guild_config.prefix}config`",
            inline=False
        )
        
        await setup_msg.edit(embed=final_embed)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'server_setup', {
            'channels_created': channels_created,
            'roles_created': roles_created
        })
    
    @commands.command(name='config')
    @commands.has_permissions(administrator=True)
    async def server_config(self, ctx, setting=None, *, value=None):
        """Configure server settings"""
        guild_config = await self.bot.db_service.get_guild_config(ctx.guild.id)
        
        if not setting:
            embed = await self.bot.create_embed(
                "⚙️ Gothic Manor Configuration",
                "Configure thy server settings with Victorian precision."
            )
            embed.add_field(
                name="📋 Available Settings",
                value="• `prefix` - Command prefix\n• `currency` - Currency name\n• `daily_reward` - Daily check-in reward\n• `welcome_channel` - Welcome channel\n• `mod_log_channel` - Moderation log channel",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}config <setting> <value>`",
                inline=False
            )
            
            if guild_config:
                embed.add_field(
                    name="📊 Current Settings",
                    value=f"**Prefix:** {guild_config.prefix}\n**Currency:** {guild_config.currency_name} {guild_config.currency_symbol}\n**Daily Reward:** {guild_config.daily_reward}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return
        
        if not value:
            embed = await self.bot.create_embed(
                "Missing Value",
                f"Please provide a value for the setting `{setting}`."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Update settings
        setting = setting.lower()
        
        if setting == 'prefix':
            if len(value) > 5:
                embed = await self.bot.create_embed(
                    "Invalid Prefix",
                    "Prefix must be 5 characters or fewer."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            
            guild_config.prefix = value
            
        elif setting == 'currency':
            guild_config.currency_name = value
            
        elif setting == 'daily_reward':
            try:
                amount = int(value)
                if amount < 1 or amount > 10000:
                    raise ValueError
                guild_config.daily_reward = amount
            except ValueError:
                embed = await self.bot.create_embed(
                    "Invalid Amount",
                    "Daily reward must be between 1 and 10,000."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
        
        elif setting == 'welcome_channel':
            try:
                channel = await commands.TextChannelConverter().convert(ctx, value)
                guild_config.welcome_channel = str(channel.id)
            except commands.BadArgument:
                embed = await self.bot.create_embed(
                    "Invalid Channel",
                    "Please mention a valid text channel."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
        
        elif setting == 'mod_log_channel':
            try:
                channel = await commands.TextChannelConverter().convert(ctx, value)
                guild_config.mod_log_channel = str(channel.id)
            except commands.BadArgument:
                embed = await self.bot.create_embed(
                    "Invalid Channel",
                    "Please mention a valid text channel."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
        
        else:
            embed = await self.bot.create_embed(
                "Unknown Setting",
                f"The setting `{setting}` is not recognized."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Save changes
        from main import db
        db.session.commit()
        
        embed = await self.bot.create_embed(
            "⚙️ Configuration Updated",
            f"Setting `{setting}` has been updated to `{value}` with Gothic precision!"
        )
        
        await ctx.send(embed=embed)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'config_update', {
            'setting': setting,
            'value': str(value)
        })
    
    @commands.command(name='restart')
    @commands.has_permissions(administrator=True)
    async def restart_bot(self, ctx):
        """Restart the bot (requires proper hosting setup)"""
        embed = await self.bot.create_embed(
            "🔄 Gothic Manor Restart",
            "Attempting to restart the Gothic manor systems..."
        )
        
        msg = await ctx.send(embed=embed)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'bot_restart', {})
        
        # In a real deployment, this would trigger a restart
        # For now, we'll just show a message
        restart_embed = await self.bot.create_embed(
            "⚠️ Restart Notice",
            "Bot restart has been requested. The manor will return shortly with renewed Gothic vigor."
        )
        restart_embed.add_field(
            name="💡 Note",
            value="In a production environment, this would restart the bot process.",
            inline=False
        )
        
        await msg.edit(embed=restart_embed)
    
    @commands.command(name='status')
    @commands.has_permissions(manage_guild=True)
    async def bot_status(self, ctx):
        """Show bot status and statistics"""
        embed = await self.bot.create_embed(
            "🏰 Gothic Manor Status",
            "Current state of the RosethornBot systems"
        )
        
        # Basic stats
        embed.add_field(
            name="🏰 Guilds",
            value=str(len(self.bot.guilds)),
            inline=True
        )
        embed.add_field(
            name="👥 Users",
            value=str(len(self.bot.users)),
            inline=True
        )
        embed.add_field(
            name="📺 Voice Connections",
            value=str(len(self.bot.voice_clients)),
            inline=True
        )
        
        # Uptime
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else timedelta(0)
        embed.add_field(
            name="⏰ Uptime",
            value=str(uptime).split('.')[0],
            inline=True
        )
        
        # Latency
        embed.add_field(
            name="📡 Latency",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # Version
        embed.add_field(
            name="📊 Version",
            value=config.BOT_VERSION,
            inline=True
        )
        
        # Features status
        features = []
        if config.ENABLE_AI_FEATURES:
            features.append("🤖 AI Features")
        if config.ENABLE_VOICE_FEATURES:
            features.append("🎭 Voice Features")
        if config.ENABLE_SOCIAL_MONITORING:
            features.append("📱 Social Monitoring")
        
        if features:
            embed.add_field(
                name="✨ Active Features",
                value="\n".join(features),
                inline=False
            )
        
        # Recent activity
        try:
            guild_stats = await self.bot.db_service.get_guild_stats(ctx.guild.id)
            if guild_stats:
                embed.add_field(
                    name="📈 Guild Activity (24h)",
                    value=f"**Commands:** {guild_stats.get('commands', 0)}\n**Check-ins:** {guild_stats.get('checkins', 0)}\n**Tickets:** {guild_stats.get('tickets', 0)}",
                    inline=True
                )
        except:
            pass
        
        embed.set_footer(text=f"🌹 Running with Victorian excellence since {datetime.utcnow().strftime('%Y')}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='backup')
    @commands.has_permissions(administrator=True)
    async def create_backup(self, ctx):
        """Create a configuration backup"""
        embed = await self.bot.create_embed(
            "💾 Creating Gothic Archive",
            "Creating a backup of thy server configuration..."
        )
        
        msg = await ctx.send(embed=embed)
        
        try:
            # In a real implementation, this would create actual backups
            backup_data = {
                'guild_id': str(ctx.guild.id),
                'guild_name': ctx.guild.name,
                'backup_date': datetime.utcnow().isoformat(),
                'configuration': 'placeholder_for_real_backup_data'
            }
            
            backup_embed = await self.bot.create_embed(
                "✅ Gothic Archive Created",
                "Server configuration has been archived with Victorian precision!"
            )
            backup_embed.add_field(
                name="📊 Backup Details",
                value=f"**Guild:** {ctx.guild.name}\n**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n**Size:** Placeholder",
                inline=False
            )
            backup_embed.add_field(
                name="💡 Note",
                value="In production, this would create a downloadable backup file.",
                inline=False
            )
            
            await msg.edit(embed=backup_embed)
            
            await self.bot.log_action(ctx.guild.id, ctx.author.id, 'backup_create', backup_data)
            
        except Exception as e:
            error_embed = await self.bot.create_embed(
                "Backup Failed",
                "Failed to create backup archive. Please try again."
            )
            await msg.edit(embed=error_embed)
            print(f"Backup error: {e}")
    
    @commands.command(name='logs')
    @commands.has_permissions(manage_guild=True)
    async def view_logs(self, ctx, action=None, limit: int = 10):
        """View audit logs"""
        if limit > 50:
            limit = 50
        
        logs = await self.bot.db_service.get_audit_logs(ctx.guild.id, action, limit)
        
        if not logs:
            embed = await self.bot.create_embed(
                "📋 No Logs Found",
                "No audit logs found for the specified criteria."
            )
            await ctx.send(embed=embed)
            return
        
        embed = await self.bot.create_embed(
            "📋 Gothic Manor Audit Logs",
            f"Recent activity in thy Victorian realm (last {len(logs)} entries)"
        )
        
        for log in logs:
            user = ctx.guild.get_member(int(log.user_id)) if log.user_id else None
            user_name = user.display_name if user else "System"
            
            timestamp = log.timestamp.strftime('%m/%d %H:%M')
            
            embed.add_field(
                name=f"🕐 {timestamp} - {log.action.replace('_', ' ').title()}",
                value=f"**User:** {user_name}\n**Details:** {str(log.details)[:100] if log.details else 'No details'}",
                inline=False
            )
        
        embed.add_field(
            name="📖 Usage",
            value=f"`{ctx.prefix}logs [action] [limit]` - Filter by action type",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='purgedata')
    @commands.has_permissions(administrator=True)
    async def purge_data(self, ctx, data_type=None, days: int = 30):
        """Purge old data from the database"""
        if not data_type:
            embed = await self.bot.create_embed(
                "🗑️ Data Purge Options",
                "Clean up old data from the Gothic archives."
            )
            embed.add_field(
                name="📋 Available Types",
                value="• `logs` - Audit logs\n• `checkins` - Old check-in records\n• `tickets` - Closed tickets\n• `applications` - Old applications",
                inline=False
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}purgedata <type> [days]`",
                inline=False
            )
            embed.add_field(
                name="⚠️ Warning",
                value="This action cannot be undone. Use with caution.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        if days < 7:
            embed = await self.bot.create_embed(
                "Invalid Days",
                "Must specify at least 7 days for data purging."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Confirmation
        confirm_embed = await self.bot.create_embed(
            "⚠️ Confirm Data Purge",
            f"This will permanently delete {data_type} older than {days} days.\n\n**This action cannot be undone!**"
        )
        confirm_embed.add_field(
            name="Confirmation",
            value="React with ✅ to confirm or ❌ to cancel",
            inline=False
        )
        
        msg = await ctx.send(embed=confirm_embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Perform purge
                deleted_count = await self.bot.db_service.purge_old_data(data_type, days)
                
                result_embed = await self.bot.create_embed(
                    "✅ Data Purged",
                    f"Successfully purged {deleted_count} {data_type} records older than {days} days."
                )
                
                await self.bot.log_action(ctx.guild.id, ctx.author.id, 'data_purge', {
                    'type': data_type,
                    'days': days,
                    'deleted_count': deleted_count
                })
            else:
                result_embed = await self.bot.create_embed(
                    "❌ Purge Cancelled",
                    "Data purge operation has been cancelled."
                )
            
            await msg.edit(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = await self.bot.create_embed(
                "⏰ Purge Timeout",
                "Data purge confirmation timed out. Operation cancelled."
            )
            await msg.edit(embed=timeout_embed)

def setup(bot):
    bot.add_cog(AdminCommands(bot))
