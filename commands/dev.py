"""
Dev command - Development utilities for bot management.
This command is intended for bot administrators and developers.
"""
import discord
import sys
import os
from datetime import datetime
from commands import BaseCommand

class DevCommand(BaseCommand):
    """Development utilities command for bot management."""
    
    @property
    def name(self):
        return "dev"
    
    @property
    def description(self):
        return "Development utilities (admin only)"
    
    @property
    def category(self):
        return "Development"
    
    async def execute(self, ctx, *args):
        """Execute the dev command with subcommands."""
        # Check if user is bot owner (you can modify this check as needed)
        if not await self.bot.is_owner(ctx.author):
            await ctx.send("❌ This command is restricted to bot administrators.")
            return
        
        if not args:
            await self._show_help(ctx)
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "reload":
            await self._reload_commands(ctx)
        elif subcommand == "status":
            await self._show_status(ctx)
        elif subcommand == "commands":
            await self._list_commands(ctx)
        elif subcommand == "shutdown":
            await self._shutdown_bot(ctx)
        else:
            await self._show_help(ctx)
    
    async def _show_help(self, ctx):
        """Show dev command help."""
        embed = discord.Embed(
            title="🛠️ Development Commands",
            description="Available development utilities:",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="Commands",
            value="**reload** - Reload all commands\n"
                  "**status** - Show bot status\n"
                  "**commands** - List loaded commands\n"
                  "**shutdown** - Shutdown the bot",
            inline=False
        )
        
        embed.set_footer(text="⚠️ These commands are for administrators only")
        await ctx.send(embed=embed)
    
    async def _reload_commands(self, ctx):
        """Reload all bot commands."""
        try:
            old_count = len(self.bot.commands)
            new_count = self.bot.reload_commands()
            
            embed = discord.Embed(
                title="🔄 Commands Reloaded",
                description=f"Successfully reloaded commands\n"
                           f"**Before:** {old_count} commands\n"
                           f"**After:** {new_count} commands",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Reload Failed",
                description=f"Error reloading commands: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    async def _show_status(self, ctx):
        """Show detailed bot status."""
        # Calculate uptime
        if hasattr(self.bot, 'start_time') and self.bot.start_time:
            uptime = discord.utils.utcnow() - self.bot.start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        else:
            uptime_str = "Unknown"
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Basic Info",
            value=f"**Uptime:** {uptime_str}\n"
                  f"**Latency:** {round(self.bot.latency * 1000, 2)}ms\n"
                  f"**Python:** {sys.version.split()[0]}\n"
                  f"**discord.py:** {discord.__version__}",
            inline=True
        )
        
        embed.add_field(
            name="Statistics",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Users:** {len(self.bot.users)}\n"
                  f"**Commands:** {len(self.bot.commands)}\n"
                  f"**Loaded Modules:** {len(self.bot.command_loader.loaded_commands)}",
            inline=True
        )
        
        # Memory usage (if psutil is available)
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            embed.add_field(
                name="System",
                value=f"**Memory:** {memory_mb:.1f} MB\n"
                      f"**CPU:** {cpu_percent:.1f}%",
                inline=True
            )
        except ImportError:
            pass
        
        await ctx.send(embed=embed)
    
    async def _list_commands(self, ctx):
        """List all loaded commands with details."""
        embed = discord.Embed(
            title="📋 Loaded Commands",
            color=discord.Color.purple()
        )
        
        commands_by_category = {}
        
        for command in self.bot.commands:
            # Get category from command instance if available
            category = "Unknown"
            if hasattr(command, 'callback') and hasattr(command.callback, '__self__'):
                cmd_instance = command.callback.__self__
                if hasattr(cmd_instance, 'category'):
                    category = cmd_instance.category
            
            if category not in commands_by_category:
                commands_by_category[category] = []
            
            aliases_str = ""
            if command.aliases:
                aliases_str = f" ({', '.join(command.aliases)})"
            
            commands_by_category[category].append(f"**{command.name}**{aliases_str}")
        
        for category, commands in commands_by_category.items():
            embed.add_field(
                name=f"{category} ({len(commands)})",
                value="\n".join(commands),
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    async def _shutdown_bot(self, ctx):
        """Shutdown the bot gracefully."""
        embed = discord.Embed(
            title="🛑 Shutting Down",
            description="Bot is shutting down gracefully...",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
        
        # Close the bot
        await self.bot.close()

def setup(bot):
    """Setup function called by the command loader."""
    command = DevCommand(bot)
    command.setup(bot)
    return command