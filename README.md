# 🌹 Rosethorn Gaming Discord Bot

A comprehensive Discord bot designed for gaming communities, featuring role management, notifications, and interactive gaming commands.

## ✨ Features

### 🔧 Role Management
- **Create roles** with custom names and colors
- **Assign/remove roles** to/from users
- **List all server roles** with member counts
- **View user roles** for any member
- Permission-based access control

### 📢 Notifications & Announcements
- **Server announcements** with role mentions
- **Gaming session alerts** with reaction-based participation
- **Reminder system** for users
- **Welcome messages** for new members
- **Server statistics** display

### 🎮 Interactive Gaming Commands
- **Dice rolling** (customizable sides and count)
- **Coin flipping**
- **Rock Paper Scissors**
- **Magic 8-Ball** responses
- **Gaming trivia** with multiple choice questions
- **Number guessing game** with configurable ranges

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- A Discord application and bot token
- Basic knowledge of Discord server management

### Step 1: Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token (keep this secure!)
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent
   - Presence Intent

### Step 2: Bot Permissions
When inviting the bot to your server, make sure it has these permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Add Reactions
- Use Slash Commands
- Manage Roles (for role management features)
- Manage Messages (for announcements)

**Invite URL Template:**
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=268454912&scope=bot%20applications.commands
```
Replace `YOUR_BOT_CLIENT_ID` with your bot's client ID from the Discord Developer Portal.

### Step 3: Installation

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/katzthebrat/Rosethorn.git
   cd Rosethorn
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration:**
   ```bash
   cp .env.example .env
   ```

4. **Edit the `.env` file with your bot configuration:**
   ```env
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=your_guild_id_here
   BOT_PREFIX=!
   BOT_NAME=Rosethorn Gaming Bot
   BOT_VERSION=1.0.0
   NOTIFICATIONS_CHANNEL_ID=your_notifications_channel_id_here
   LOG_LEVEL=INFO
   ```

   **Configuration Options:**
   - `DISCORD_TOKEN`: Your bot token from Discord Developer Portal (required)
   - `GUILD_ID`: Your Discord server ID for command syncing (optional, leave empty for global commands)
   - `BOT_PREFIX`: Prefix for text commands (default: `!`)
   - `BOT_NAME`: Display name for your bot
   - `NOTIFICATIONS_CHANNEL_ID`: Default channel for notifications (optional)
   - `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Step 4: Running the Bot

```bash
python main.py
```

The bot will start and display connection information. You should see:
```
🌹 Rosethorn Gaming Bot v1.0.0 is ready!
Connected as: YourBotName#1234
Bot ID: 123456789012345678
Guilds: 1
Command prefix: !
```

## 📖 Usage Guide

### Slash Commands (Recommended)

The bot primarily uses Discord's slash commands for the best user experience:

#### Role Management
- `/createrole <name> [color] [reason]` - Create a new role
- `/assignrole <user> <role>` - Assign a role to a user
- `/removerole <user> <role>` - Remove a role from a user
- `/listroles` - List all server roles
- `/userroles [user]` - Show roles for a user

#### Notifications
- `/announce <message> [channel] [mention_role]` - Send an announcement
- `/gamealert <game> <time> [description]` - Create a gaming session alert
- `/reminder <message> <time_minutes> [user]` - Set a reminder
- `/welcome <user> [custom_message]` - Send a welcome message
- `/serverstats` - Display server statistics

#### Games
- `/dice [sides] [count]` - Roll dice (default: 1d6)
- `/coinflip` - Flip a coin
- `/rps <choice>` - Play Rock Paper Scissors
- `/8ball <question>` - Ask the magic 8-ball
- `/trivia` - Start a trivia question
- `/numberguess [max_number]` - Start a number guessing game
- `/guess <number>` - Make a guess in the number guessing game

### Text Commands (Legacy Support)
- `!help` - Show help information
- `!info` - Display bot information
- `!ping` - Check bot latency

## 🛡️ Permissions and Security

### Role Management Permissions
- Users need "Manage Roles" permission to create/assign roles
- Users cannot assign roles higher than their own highest role
- The bot needs "Manage Roles" permission and should be placed high in the role hierarchy

### Notification Permissions
- Users need "Manage Messages" permission for announcements and welcome messages
- All users can use gaming alerts and reminders

### Bot Safety Features
- Permission validation for all management commands
- Role hierarchy respect (can't assign higher roles)
- Input validation and error handling
- Ephemeral error messages (only visible to command user)

## 🔧 Customization

### Adding Custom Trivia Questions
Edit the `trivia_questions` list in `cogs/games.py` to add your own questions:

```python
{
    "question": "Your question here?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "answer": 0,  # Index of correct answer (0-3)
    "explanation": "Explanation of the answer"
}
```

### Modifying Game Settings
Edit `config.py` to modify game configurations:
- Dice limits (sides, count)
- Magic 8-ball responses
- Role permissions mapping

### Custom Welcome Messages
The welcome command supports custom messages, or you can modify the default in `cogs/notifications.py`.

## 🐛 Troubleshooting

### Common Issues

1. **Bot doesn't respond to commands:**
   - Check bot permissions in the server
   - Ensure the bot is online and properly configured
   - Verify the bot token is correct

2. **Slash commands not appearing:**
   - Commands may take up to 1 hour to sync globally
   - Try setting a `GUILD_ID` for faster local syncing
   - Restart the bot after configuration changes

3. **Role management not working:**
   - Ensure the bot has "Manage Roles" permission
   - Check that the bot's role is higher than roles it's trying to manage
   - Verify users have appropriate permissions

4. **Import errors:**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

### Getting Help
- Check the console output for error messages
- Enable DEBUG logging by setting `LOG_LEVEL=DEBUG` in your `.env` file
- Ensure all required environment variables are set

## 📝 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

**Made with ❤️ for gaming communities**
