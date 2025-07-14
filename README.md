# 🌹 Rosethorn Discord Bot

A modular Discord bot built with Python and discord.py, featuring dynamic command loading and an extensible architecture.

## ✨ Features

- **Modular Architecture**: Each command is a separate file for easy management
- **Dynamic Loading**: Commands are loaded automatically from the `commands/` directory
- **Hot Reloading**: Reload commands without restarting the bot (perfect for development)
- **Extensible Design**: Easy to add new commands with consistent structure
- **Error Handling**: Comprehensive error handling and logging
- **Configuration Management**: Environment-based configuration with `.env` support
- **Member Onboarding**: Automated new member registration system with admin approval workflow

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Discord bot token (see [Discord Developer Portal](https://discord.com/developers/applications))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/katzthebrat/Rosethorn.git
   cd Rosethorn
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Discord bot token:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   COMMAND_PREFIX=!
   BOT_DESCRIPTION=Rosethorn - A modular Discord bot
   DEBUG=False
   
   # Onboarding system (optional)
   ONBOARDING_CHANNEL_ID=1311529665348767835
   ONBOARDING_ROLE_ID=1308905911489921124
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 📁 Project Structure

```
Rosethorn/
├── bot.py                 # Main bot file
├── config.py             # Configuration management
├── command_loader.py     # Dynamic command loading system
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── .gitignore          # Git ignore rules
├── commands/           # Commands directory
│   ├── __init__.py    # Base command class
│   ├── ping.py        # Ping command
│   ├── help.py        # Custom help command
│   └── info.py        # Bot information command
└── README.md          # This file
```

## 🛠️ Built-in Features

### Commands
| Command | Description | Aliases |
|---------|-------------|---------|
| `!ping` | Check bot latency and responsiveness | - |
| `!help` | Show available commands | `h`, `commands` |
| `!info` | Display bot and server information | `about`, `botinfo` |

### Onboarding System
- **Automatic Welcome**: Detects new members and sends welcome DMs with registration forms
- **Data Collection**: Collects preferred name, gamertag, and birthday through interactive modals
- **Admin Review**: Sends member information to designated admin channel with approval buttons
- **Member Management**: Automatically sets nicknames and manages approval workflow

See [ONBOARDING.md](ONBOARDING.md) for detailed documentation on the onboarding system.

## 🔧 Adding New Commands

Creating a new command is simple! Follow these steps:

### 1. Create a New Command File

Create a new Python file in the `commands/` directory. For example, `commands/hello.py`:

```python
"""
Hello command - A simple greeting command.
"""
import discord
from commands import BaseCommand

class HelloCommand(BaseCommand):
    """Simple hello command that greets users."""
    
    @property
    def name(self):
        return "hello"
    
    @property
    def description(self):
        return "Say hello to the bot"
    
    @property
    def aliases(self):
        return ["hi", "greet"]
    
    @property
    def category(self):
        return "Fun"
    
    async def execute(self, ctx, *args):
        """Execute the hello command."""
        user = ctx.author.display_name
        await ctx.send(f"Hello, {user}! 👋")

def setup(bot):
    """Setup function called by the command loader."""
    command = HelloCommand(bot)
    command.setup(bot)
    return command
```

### 2. Command Structure Requirements

Each command file must:

- **Inherit from `BaseCommand`**: Import and extend the base class
- **Implement required properties**:
  - `name`: The command name (string)
  - `description`: Command description for help (string)
- **Implement required methods**:
  - `execute(ctx, *args)`: The main command logic
- **Include a `setup(bot)` function**: For command registration

### 3. Optional Properties

- `aliases`: List of alternative command names
- `category`: Command category for organization

### 4. Restart or Reload

The bot will automatically discover and load your new command when:
- The bot is restarted, or
- Commands are manually reloaded (if you implement a reload command)

## 🔄 Hot Reloading (Development)

For development, you can add a reload command to dynamically reload all commands without restarting the bot. This is useful when making changes to existing commands.

## 🎛️ Configuration Options

The bot uses environment variables for configuration. Available options:

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Your Discord bot token | **Required** |
| `COMMAND_PREFIX` | Command prefix | `!` |
| `BOT_DESCRIPTION` | Bot description | `Rosethorn - A modular Discord bot` |
| `DEBUG` | Enable debug logging | `False` |

## 📋 Command Categories

Organize your commands by setting the `category` property:

- **Utility**: Helper commands (ping, help, info)
- **Fun**: Entertainment commands
- **Moderation**: Server management commands
- **Games**: Game-related commands
- **Music**: Audio/music commands

## 🔍 Error Handling

The bot includes comprehensive error handling:

- **Command Not Found**: Suggests using help command
- **Missing Arguments**: Shows which argument is missing
- **Permission Errors**: Informs about insufficient permissions
- **Unexpected Errors**: Logs error details and shows user-friendly message

## 📝 Logging

The bot logs important events:

- Command usage
- Error occurrences
- Bot startup/shutdown
- Command loading status

Logs are output to console and optionally to `bot.log` file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the logs for error messages
2. Ensure your Discord token is valid
3. Verify all dependencies are installed
4. Check that the bot has necessary permissions in your Discord server

## 🚀 Advanced Usage

### Custom Base Commands

You can extend the `BaseCommand` class to create specialized command types:

```python
class AdminCommand(BaseCommand):
    """Base class for admin-only commands."""
    
    async def execute(self, ctx, *args):
        # Check for admin permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ This command requires administrator permissions.")
            return
        
        # Call the actual command implementation
        await self.admin_execute(ctx, *args)
    
    @abstractmethod
    async def admin_execute(self, ctx, *args):
        """Override this method in admin commands."""
        pass
```

### Database Integration

For commands that need data persistence, consider integrating a database:

```python
import sqlite3
# or
import asyncpg  # for PostgreSQL
# or
from motor.motor_asyncio import AsyncIOMotorClient  # for MongoDB
```

### External API Integration

Commands can easily integrate with external APIs:

```python
import aiohttp

async def fetch_data(self, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

---

Made with ❤️ by [katzthebrat](https://github.com/katzthebrat)
