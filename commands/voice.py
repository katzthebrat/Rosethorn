import discord
from discord.ext import commands
import asyncio
import config

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='join')
    async def join_voice(self, ctx):
        """Join the user's voice channel"""
        if not ctx.author.voice:
            embed = await self.bot.create_embed(
                "Not in Voice Channel",
                "Thou must be in a voice chamber for me to join thee."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            if ctx.voice_client.channel == channel:
                embed = await self.bot.create_embed(
                    "Already Connected",
                    f"I am already gracing {channel.mention} with my Gothic presence."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            else:
                await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        embed = await self.bot.create_embed(
            "🎭 Joined Voice Chamber",
            f"I have entered {channel.mention} to share in thy Gothic discourse."
        )
        embed.add_field(
            name="Available Commands",
            value=f"`{ctx.prefix}speak <message>` - Speak with Victorian elegance\n`{ctx.prefix}leave` - Depart the chamber",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'voice_join', {
            'channel': channel.name
        })
    
    @commands.command(name='leave', aliases=['disconnect'])
    async def leave_voice(self, ctx):
        """Leave the voice channel"""
        if not ctx.voice_client:
            embed = await self.bot.create_embed(
                "Not Connected",
                "I am not currently in any voice chamber."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        
        embed = await self.bot.create_embed(
            "🚪 Departed Voice Chamber",
            f"I have gracefully departed from **{channel_name}**. Until we meet again in the Gothic halls."
        )
        
        await ctx.send(embed=embed)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'voice_leave', {
            'channel': channel_name
        })
    
    @commands.command(name='speak', aliases=['say', 'tts'])
    async def text_to_speech(self, ctx, *, message=None):
        """Speak a message with text-to-speech"""
        if not message:
            embed = await self.bot.create_embed(
                "Gothic Speech System",
                "Let my Victorian voice grace thy ears with elegant speech."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}speak <your message>`",
                inline=False
            )
            embed.add_field(
                name="💡 Note",
                value="I must be in a voice channel to speak. Use `r!join` first.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        if not ctx.voice_client:
            embed = await self.bot.create_embed(
                "Not in Voice Channel",
                "I must be in a voice chamber to speak. Use `r!join` first."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if voice service is available
        if not config.ENABLE_VOICE_FEATURES:
            embed = await self.bot.create_embed(
                "Voice Features Disabled",
                "The Gothic voice features are currently disabled in this manor."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Limit message length
        if len(message) > 500:
            embed = await self.bot.create_embed(
                "Message Too Long",
                "Please limit thy Gothic proclamations to 500 characters."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Generate and play speech
        try:
            embed = await self.bot.create_embed(
                "🎭 Speaking with Victorian Grace",
                f"*\"{message}\"*"
            )
            embed.add_field(
                name="Speaker",
                value=ctx.author.mention,
                inline=True
            )
            embed.add_field(
                name="Channel",
                value=ctx.voice_client.channel.mention,
                inline=True
            )
            
            await ctx.send(embed=embed)
            
            # Use voice service to generate and play audio
            audio_file = await self.bot.voice_service.text_to_speech(message)
            
            if audio_file:
                source = discord.FFmpegPCMAudio(audio_file)
                ctx.voice_client.play(source)
                
                # Wait for playback to finish
                while ctx.voice_client.is_playing():
                    await asyncio.sleep(0.1)
                
                # Clean up audio file
                import os
                try:
                    os.remove(audio_file)
                except:
                    pass
            else:
                error_embed = await self.bot.create_embed(
                    "Speech Generation Failed",
                    "Alas, I could not generate the Gothic speech at this time."
                )
                await ctx.send(embed=error_embed, delete_after=10)
            
        except Exception as e:
            embed = await self.bot.create_embed(
                "Speech Error",
                "An error occurred while attempting to speak in the Gothic manner."
            )
            await ctx.send(embed=embed, delete_after=10)
            print(f"TTS Error: {e}")
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'voice_speak', {
            'message': message[:100],
            'channel': ctx.voice_client.channel.name
        })
    
    @commands.command(name='announce')
    @commands.has_permissions(manage_guild=True)
    async def voice_announce(self, ctx, channel: discord.VoiceChannel = None, *, message=None):
        """Make an announcement in a voice channel"""
        if not message:
            embed = await self.bot.create_embed(
                "Gothic Announcement System",
                "Broadcast thy important message to the voice chambers."
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}announce [#voice-channel] <message>`",
                inline=False
            )
            embed.add_field(
                name="💡 Note",
                value="If no channel is specified, I will use thy current voice channel.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        # Determine target channel
        target_channel = channel
        if not target_channel:
            if ctx.author.voice:
                target_channel = ctx.author.voice.channel
            else:
                embed = await self.bot.create_embed(
                    "No Voice Channel",
                    "Please specify a voice channel or join one thyself."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
        
        # Connect to channel if not already connected
        voice_client = ctx.voice_client
        if not voice_client or voice_client.channel != target_channel:
            if voice_client:
                await voice_client.move_to(target_channel)
            else:
                voice_client = await target_channel.connect()
        
        # Create announcement embed
        announce_embed = await self.bot.create_embed(
            "📢 Gothic Manor Announcement",
            f"**Announcement in {target_channel.mention}:**\n\n*\"{message}\"*"
        )
        announce_embed.add_field(
            name="Announced by",
            value=ctx.author.mention,
            inline=True
        )
        announce_embed.add_field(
            name="Time",
            value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>",
            inline=True
        )
        
        await ctx.send(embed=announce_embed)
        
        # Speak the announcement
        try:
            if config.ENABLE_VOICE_FEATURES:
                # Add formal announcement prefix
                formal_message = f"Attention residents of the Gothic manor. {message}"
                
                audio_file = await self.bot.voice_service.text_to_speech(formal_message)
                
                if audio_file:
                    source = discord.FFmpegPCMAudio(audio_file)
                    voice_client.play(source)
                    
                    # Wait for playback
                    while voice_client.is_playing():
                        await asyncio.sleep(0.1)
                    
                    # Clean up
                    import os
                    try:
                        os.remove(audio_file)
                    except:
                        pass
        except Exception as e:
            print(f"Announcement TTS Error: {e}")
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'voice_announce', {
            'message': message[:100],
            'channel': target_channel.name
        })
    
    @commands.command(name='voicestats')
    async def voice_statistics(self, ctx):
        """Show voice channel statistics"""
        embed = await self.bot.create_embed(
            "🎭 Voice Chamber Statistics",
            "Current state of the Gothic manor's voice chambers"
        )
        
        # Count voice channels and users
        voice_channels = len(ctx.guild.voice_channels)
        users_in_voice = sum(len(vc.members) for vc in ctx.guild.voice_channels)
        
        embed.add_field(
            name="🏰 Total Voice Chambers",
            value=str(voice_channels),
            inline=True
        )
        embed.add_field(
            name="👥 Users in Voice",
            value=str(users_in_voice),
            inline=True
        )
        embed.add_field(
            name="🤖 Bot Status",
            value="Connected" if ctx.voice_client else "Not Connected",
            inline=True
        )
        
        # Show active channels
        active_channels = [vc for vc in ctx.guild.voice_channels if vc.members]
        
        if active_channels:
            channel_info = []
            for vc in active_channels[:5]:  # Show first 5
                member_count = len(vc.members)
                channel_info.append(f"**{vc.name}** - {member_count} member{'s' if member_count != 1 else ''}")
            
            embed.add_field(
                name="🎪 Active Chambers",
                value="\n".join(channel_info),
                inline=False
            )
        
        # Bot's current channel if connected
        if ctx.voice_client:
            embed.add_field(
                name="🎭 Current Chamber",
                value=f"{ctx.voice_client.channel.mention} ({len(ctx.voice_client.channel.members)} members)",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def summon_to_channel(self, ctx, channel: discord.VoiceChannel):
        """Summon the bot to a specific voice channel"""
        if ctx.voice_client:
            if ctx.voice_client.channel == channel:
                embed = await self.bot.create_embed(
                    "Already Present",
                    f"I am already gracing {channel.mention} with my Gothic presence."
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            else:
                await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        
        embed = await self.bot.create_embed(
            "🌙 Summoned to Voice Chamber",
            f"I have been summoned to {channel.mention} by thy noble command."
        )
        
        await ctx.send(embed=embed)
        
        await self.bot.log_action(ctx.guild.id, ctx.author.id, 'voice_summon', {
            'channel': channel.name
        })

def setup(bot):
    bot.add_cog(VoiceCommands(bot))
