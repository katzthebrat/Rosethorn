#!/usr/bin/env python3
"""
Simple startup script for the Rosethorn Discord bot.
This script handles basic setup and provides helpful error messages.
"""

import sys
import os
from pathlib import Path

def check_requirements():
    """Check if all requirements are met before starting the bot."""
    print("🌹 Rosethorn Discord Bot Startup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Please copy .env.example to .env and configure your bot token")
        print("   Command: cp .env.example .env")
        return False
    
    print("✅ Configuration file found")
    
    # Check if discord.py is installed
    try:
        import discord
        print(f"✅ discord.py version: {discord.__version__}")
    except ImportError:
        print("❌ discord.py not installed!")
        print("   Please install requirements: pip install -r requirements.txt")
        return False
    
    # Check if commands directory exists
    commands_dir = Path("commands")
    if not commands_dir.exists():
        print("❌ Commands directory not found!")
        return False
    
    # Count command files
    command_files = list(commands_dir.glob("*.py"))
    command_files = [f for f in command_files if not f.name.startswith("__")]
    print(f"✅ Found {len(command_files)} command files")
    
    print("=" * 40)
    return True

def main():
    """Main startup function."""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Startup checks failed. Please fix the issues above and try again.")
        return 1
    
    print("🚀 Starting bot...")
    print("   Press Ctrl+C to stop the bot")
    print("=" * 40)
    
    # Import and run the bot
    try:
        from bot import main as bot_main
        import asyncio
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())