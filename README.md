# Rosethorn Discord Bot

A Discord bot with a comprehensive ticket system for managing user support requests.

## Features

- `/tickets` slash command with support for 4 ticket types:
  - **Permissions** - Issues related to permissions and access
  - **General** - General questions and support  
  - **Report** - Report violations or issues
  - **Defense Submission** - Submit defense materials

- Automatic ticket channel creation in specified category
- Admin controls for claiming and closing tickets
- Detailed ticket transcripts on closure
- User information collection (preferred name, gamertag, issue details)

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure the bot:**
   - Copy `config.example.json` to `config.json`
   - Fill in your Discord bot token, client ID, guild ID, and ticket category ID

3. **Deploy slash commands:**
   ```bash
   npm run deploy
   ```

4. **Start the bot:**
   ```bash
   npm start
   ```

## Configuration

Edit `config.json` with your Discord bot credentials:

- `token`: Your Discord bot token
- `clientId`: Your Discord application client ID  
- `guildId`: The Discord server ID where commands will be deployed
- `ticketCategoryId`: The category channel ID where tickets will be created (default: 1313028919997239297)
- `adminRoles`: Array of role names that can claim/close tickets (e.g., ["Admin", "Moderator", "Staff"])

## Usage

1. Use `/tickets` command to display the ticket selection interface
2. Users click buttons to create tickets of different types
3. Admins can claim and close tickets using the provided buttons
4. On closure, a detailed summary and transcript are generated

## Permissions

The bot requires the following permissions:
- Send Messages
- Manage Channels
- Read Message History
- Use Slash Commands
- Embed Links
- Attach Files 
