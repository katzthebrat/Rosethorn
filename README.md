# Rosethorn Discord Bot

A modern Discord bot built with slash commands using Discord.js v14. Rosethorn features a modular command structure where each slash command is implemented as a separate file for easy maintenance and development.

## Features

- ✨ **Slash Commands**: All commands are implemented as modern Discord slash commands
- 📁 **Modular Structure**: Each command is in its own file for easy organization
- 🔧 **Easy Configuration**: Simple JSON configuration file
- 🚀 **Auto-deployment**: Scripts to deploy commands to Discord's API
- 📊 **Built-in Commands**: Utility, info, and fun commands included

## Setup

### Prerequisites

- Node.js 16.11.0 or higher
- A Discord Bot Token
- Discord Application ID

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Rosethorn
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure the bot:
   - Copy `config.json` and fill in your bot details:
   ```json
   {
     "token": "YOUR_BOT_TOKEN_HERE",
     "clientId": "YOUR_APPLICATION_ID_HERE",
     "guildId": "YOUR_GUILD_ID_HERE"
   }
   ```

4. Deploy slash commands:
   ```bash
   # For testing in a specific guild (faster)
   npm run deploy
   
   # For global commands (takes up to 1 hour to propagate)
   npm run deploy-global
   ```

5. Start the bot:
   ```bash
   npm start
   ```

## Command Structure

Commands are organized in the `commands/` directory by category:

```
commands/
├── info/
│   ├── serverinfo.js
│   └── userinfo.js
├── utility/
│   └── ping.js
└── fun/
    └── echo.js
```

## Adding New Slash Commands

### 1. Create Command File

Create a new `.js` file in the appropriate category folder under `commands/`. Each command file should export an object with `data` and `execute` properties:

```javascript
const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('commandname')
        .setDescription('Command description')
        // Add options here if needed
        .addStringOption(option =>
            option.setName('input')
                .setDescription('Description of the option')
                .setRequired(true)),
    async execute(interaction) {
        // Command logic here
        await interaction.reply('Hello World!');
    },
};
```

### 2. Command Options

Discord.js supports various option types:

- `.addStringOption()` - Text input
- `.addIntegerOption()` - Number input
- `.addBooleanOption()` - True/false
- `.addUserOption()` - User mention
- `.addChannelOption()` - Channel mention
- `.addRoleOption()` - Role mention
- `.addAttachmentOption()` - File upload

### 3. Deploy Commands

After creating new commands, deploy them to Discord:

```bash
# For guild-specific (testing)
npm run deploy

# For global (production)
npm run deploy-global
```

### 4. Command Categories

Organize commands into logical categories by creating subdirectories:

- `info/` - Information commands (serverinfo, userinfo, etc.)
- `utility/` - Utility commands (ping, help, etc.)
- `fun/` - Entertainment commands (games, jokes, etc.)
- `moderation/` - Moderation commands (kick, ban, etc.)
- `admin/` - Administrative commands

## Available Commands

### Utility Commands
- `/ping` - Shows bot latency and API response time

### Info Commands
- `/serverinfo` - Displays server information
- `/userinfo [user]` - Shows user information (defaults to command user)

### Fun Commands
- `/echo <input>` - Echoes back your input

## Development

### Project Structure

```
Rosethorn/
├── commands/           # Slash command files organized by category
│   ├── info/
│   ├── utility/
│   └── fun/
├── events/            # Event handlers (for future expansion)
├── index.js           # Main bot file
├── deploy-commands.js # Guild command deployment
├── deploy-global-commands.js # Global command deployment
├── config.json        # Bot configuration
├── package.json       # Node.js dependencies
└── README.md          # This file
```

### Best Practices

1. **One command per file**: Keep each slash command in its own file
2. **Descriptive names**: Use clear, descriptive command and option names
3. **Error handling**: Always handle errors gracefully in your commands
4. **Permissions**: Set appropriate permissions for commands that require them
5. **Documentation**: Comment your code and update this README when adding features

### Adding Permissions

To add permissions to a command, use the `setDefaultMemberPermissions()` method:

```javascript
.setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages)
```

### Error Handling

Always wrap command execution in try-catch blocks and provide user feedback:

```javascript
try {
    await command.execute(interaction);
} catch (error) {
    console.error(error);
    await interaction.reply({ 
        content: 'There was an error while executing this command!', 
        ephemeral: true 
    });
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your commands following the established structure
4. Test your changes
5. Submit a pull request

## License

This project is licensed under the ISC License. 
