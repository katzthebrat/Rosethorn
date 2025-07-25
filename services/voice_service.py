import os
import asyncio
import discord
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime
from main import db
from models import VoiceSession, BotLog

logger = logging.getLogger(__name__)

class VoiceService:
    """Voice channel management and text-to-speech functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}  # Guild ID -> VoiceClient
        self.tts_settings = {}   # Guild ID -> TTS settings
        
        # Default TTS settings
        self.default_tts_settings = {
            'voice': 'female',
            'speed': 1.0,
            'pitch': 1.0,
            'volume': 0.8,
            'language': 'en-US'
        }
        
        # TTS API configuration
        self.tts_api_key = os.getenv('TTS_API_KEY', '')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', '')
        
    async def join_voice_channel(self, ctx, channel=None):
        """Join a voice channel."""
        if channel is None:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                embed = discord.Embed(
                    title="❌ No Voice Channel",
                    description="You need to be in a voice channel or specify one.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
                return None
        
        try:
            # Leave current channel if connected
            if ctx.guild.id in self.voice_clients:
                await self.leave_voice_channel(ctx.guild.id)
            
            # Join the new channel
            voice_client = await channel.connect()
            self.voice_clients[ctx.guild.id] = voice_client
            
            # Log voice connection
            await self.log_voice_event(
                guild_id=str(ctx.guild.id),
                action="joined_channel",
                channel_id=str(channel.id),
                user_id=str(ctx.author.id)
            )
            
            embed = discord.Embed(
                title="🔊 Voice Channel Joined",
                description=f"Connected to {channel.mention}",
                color=0x711417
            )
            embed.set_footer(text="Ready for voice commands 🌹")
            
            await ctx.send(embed=embed)
            return voice_client
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="I don't have permission to join that voice channel.",
                color=0x711417
            )
            await ctx.send(embed=embed)
            return None
        
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            embed = discord.Embed(
                title="❌ Connection Error",
                description="Failed to join the voice channel.",
                color=0x711417
            )
            await ctx.send(embed=embed)
            return None
    
    async def leave_voice_channel(self, guild_id):
        """Leave a voice channel."""
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
            
            # Log voice disconnection
            await self.log_voice_event(
                guild_id=str(guild_id),
                action="left_channel"
            )
            
            return True
        return False
    
    async def text_to_speech(self, ctx, text, voice_settings=None):
        """Convert text to speech and play in voice channel."""
        # Check if bot is in voice channel
        if ctx.guild.id not in self.voice_clients:
            await self.join_voice_channel(ctx)
            if ctx.guild.id not in self.voice_clients:
                return
        
        voice_client = self.voice_clients[ctx.guild.id]
        
        # Get TTS settings for guild
        settings = self.tts_settings.get(ctx.guild.id, self.default_tts_settings.copy())
        if voice_settings:
            settings.update(voice_settings)
        
        try:
            # Generate TTS audio
            audio_data = await self.generate_tts_audio(text, settings)
            
            if audio_data:
                # Create audio source
                audio_source = discord.FFmpegPCMAudio(audio_data, pipe=True)
                
                # Play audio
                if not voice_client.is_playing():
                    voice_client.play(audio_source)
                    
                    # Log TTS usage
                    await self.log_voice_event(
                        guild_id=str(ctx.guild.id),
                        action="tts_played",
                        user_id=str(ctx.author.id),
                        details={"text_length": len(text), "voice": settings['voice']}
                    )
                    
                    embed = discord.Embed(
                        title="🗣️ Text-to-Speech",
                        description="Playing audio in voice channel...",
                        color=0x711417
                    )
                    embed.add_field(name="Text", value=text[:100] + ("..." if len(text) > 100 else ""), inline=False)
                    embed.set_footer(text="Spoken with Victorian elegance 🌹")
                    
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="🔊 Audio Playing",
                        description="Please wait for the current audio to finish.",
                        color=0x711417
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ TTS Error",
                    description="Failed to generate speech audio.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            embed = discord.Embed(
                title="❌ TTS Error",
                description="An error occurred while generating speech.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def generate_tts_audio(self, text, settings):
        """Generate TTS audio using available APIs."""
        # Try ElevenLabs first (high quality)
        if self.elevenlabs_api_key:
            audio_data = await self.generate_elevenlabs_tts(text, settings)
            if audio_data:
                return audio_data
        
        # Fallback to other TTS services
        if self.tts_api_key:
            audio_data = await self.generate_generic_tts(text, settings)
            if audio_data:
                return audio_data
        
        # Use system TTS as last resort
        return await self.generate_system_tts(text, settings)
    
    async def generate_elevenlabs_tts(self, text, settings):
        """Generate TTS using ElevenLabs API."""
        try:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (female)
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
            
            return None
        
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None
    
    async def generate_generic_tts(self, text, settings):
        """Generate TTS using generic API."""
        try:
            # Implement your preferred TTS API here
            # This is a placeholder for other TTS services
            return None
        
        except Exception as e:
            logger.error(f"Generic TTS error: {e}")
            return None
    
    async def generate_system_tts(self, text, settings):
        """Generate TTS using system tools (fallback)."""
        try:
            # This would use system TTS tools like espeak or festival
            # For now, return None as system TTS requires additional setup
            return None
        
        except Exception as e:
            logger.error(f"System TTS error: {e}")
            return None
    
    async def set_voice_settings(self, ctx, **settings):
        """Set voice/TTS settings for the guild."""
        guild_settings = self.tts_settings.get(ctx.guild.id, self.default_tts_settings.copy())
        
        # Update settings
        valid_settings = ['voice', 'speed', 'pitch', 'volume', 'language']
        updated = []
        
        for key, value in settings.items():
            if key in valid_settings:
                guild_settings[key] = value
                updated.append(f"{key}: {value}")
        
        if updated:
            self.tts_settings[ctx.guild.id] = guild_settings
            
            embed = discord.Embed(
                title="🎛️ Voice Settings Updated",
                description="TTS settings have been modified.",
                color=0x711417
            )
            embed.add_field(
                name="Updated Settings",
                value="\n".join(updated),
                inline=False
            )
            embed.set_footer(text="Settings applied to future TTS messages 🌹")
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Invalid Settings",
                description="No valid settings were provided.",
                color=0x711417
            )
            embed.add_field(
                name="Valid Settings",
                value="voice, speed, pitch, volume, language",
                inline=False
            )
            await ctx.send(embed=embed)
    
    async def play_audio_file(self, ctx, file_path):
        """Play an audio file in voice channel."""
        if ctx.guild.id not in self.voice_clients:
            await self.join_voice_channel(ctx)
            if ctx.guild.id not in self.voice_clients:
                return
        
        voice_client = self.voice_clients[ctx.guild.id]
        
        try:
            if not voice_client.is_playing():
                audio_source = discord.FFmpegPCMAudio(file_path)
                voice_client.play(audio_source)
                
                embed = discord.Embed(
                    title="🎵 Playing Audio",
                    description="Audio file is now playing in voice channel.",
                    color=0x711417
                )
                embed.set_footer(text="Enjoy the Victorian soundtrack 🌹")
                
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="🔊 Audio Playing",
                    description="Please wait for the current audio to finish.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Error playing audio file: {e}")
            embed = discord.Embed(
                title="❌ Playback Error",
                description="Failed to play the audio file.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def stop_audio(self, ctx):
        """Stop currently playing audio."""
        if ctx.guild.id in self.voice_clients:
            voice_client = self.voice_clients[ctx.guild.id]
            
            if voice_client.is_playing():
                voice_client.stop()
                
                embed = discord.Embed(
                    title="⏹️ Audio Stopped",
                    description="Playback has been stopped.",
                    color=0x711417
                )
                embed.set_footer(text="Silence returns to the manor 🌹")
                
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="🔇 No Audio Playing",
                    description="There is no audio currently playing.",
                    color=0x711417
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="I'm not connected to a voice channel.",
                color=0x711417
            )
            await ctx.send(embed=embed)
    
    async def track_voice_activity(self, member, before, after):
        """Track voice channel activity."""
        if member.bot:
            return
        
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        
        # User left voice channel
        if before.channel and not after.channel:
            await self.end_voice_session(guild_id, user_id, str(before.channel.id))
        
        # User joined voice channel
        elif not before.channel and after.channel:
            await self.start_voice_session(guild_id, user_id, str(after.channel.id))
        
        # User switched voice channels
        elif before.channel and after.channel and before.channel != after.channel:
            await self.end_voice_session(guild_id, user_id, str(before.channel.id))
            await self.start_voice_session(guild_id, user_id, str(after.channel.id))
    
    async def start_voice_session(self, guild_id, user_id, channel_id):
        """Start tracking a voice session."""
        with self.bot.app_context:
            session = VoiceSession(
                guild_id=guild_id,
                user_id=user_id,
                channel_id=channel_id,
                joined_at=datetime.utcnow()
            )
            db.session.add(session)
            db.session.commit()
    
    async def end_voice_session(self, guild_id, user_id, channel_id):
        """End a voice session and calculate duration."""
        with self.bot.app_context:
            session = VoiceSession.query.filter_by(
                guild_id=guild_id,
                user_id=user_id,
                channel_id=channel_id,
                left_at=None
            ).first()
            
            if session:
                now = datetime.utcnow()
                session.left_at = now
                session.duration_seconds = int((now - session.joined_at).total_seconds())
                db.session.commit()
    
    async def get_voice_stats(self, guild_id, user_id=None):
        """Get voice activity statistics."""
        with self.bot.app_context:
            query = VoiceSession.query.filter_by(guild_id=str(guild_id))
            
            if user_id:
                query = query.filter_by(user_id=str(user_id))
            
            sessions = query.filter(VoiceSession.duration_seconds.isnot(None)).all()
            
            total_time = sum(session.duration_seconds for session in sessions)
            session_count = len(sessions)
            
            if session_count > 0:
                average_time = total_time / session_count
            else:
                average_time = 0
            
            return {
                'total_time': total_time,
                'session_count': session_count,
                'average_time': average_time
            }
    
    async def log_voice_event(self, guild_id, action, channel_id=None, user_id=None, details=None):
        """Log voice-related events."""
        with self.bot.app_context:
            log_entry = BotLog(
                guild_id=guild_id,
                level="INFO",
                module="voice",
                message=f"Voice event: {action}",
                user_id=user_id,
                channel_id=channel_id,
                extra_data={
                    "action": action,
                    **(details or {})
                }
            )
            db.session.add(log_entry)
            db.session.commit()
    
    async def cleanup_voice_connections(self):
        """Cleanup voice connections on shutdown."""
        for guild_id, voice_client in self.voice_clients.items():
            try:
                await voice_client.disconnect()
            except:
                pass
        
        self.voice_clients.clear()
