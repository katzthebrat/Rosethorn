const { Client, GatewayIntentBits, Collection } = require('discord.js');
const { token } = require('./config.json');
const fs = require('fs');

// Create a new client instance
const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ] 
});

// Create collections for commands and interactions
client.commands = new Collection();
client.tickets = new Collection(); // Store active tickets

// Load commands
const commandFiles = fs.readdirSync('./commands').filter(file => file.endsWith('.js'));
for (const file of commandFiles) {
    const command = require(`./commands/${file}`);
    client.commands.set(command.data.name, command);
}

// Ready event
client.once('ready', () => {
    console.log(`Ready! Logged in as ${client.user.tag}`);
});

// Interaction handling
client.on('interactionCreate', async interaction => {
    // Handle slash commands
    if (interaction.isChatInputCommand()) {
        const command = client.commands.get(interaction.commandName);
        if (!command) return;

        try {
            await command.execute(interaction);
        } catch (error) {
            console.error(error);
            await interaction.reply({ content: 'There was an error while executing this command!', ephemeral: true });
        }
    }
    
    // Handle button interactions
    if (interaction.isButton()) {
        const { handleTicketButton } = require('./handlers/ticketHandler');
        await handleTicketButton(interaction);
    }
    
    // Handle modal submissions
    if (interaction.isModalSubmit()) {
        const { handleModalSubmit } = require('./handlers/ticketHandler');
        await handleModalSubmit(interaction);
    }
});

// Login to Discord
client.login(token);

module.exports = client;