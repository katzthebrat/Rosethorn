const { Client, Collection, Events, GatewayIntentBits } = require('discord.js');
const fs = require('node:fs');
const path = require('node:path');

// Load configuration from config.json or environment variables
let config;
try {
	config = require('./config.json');
} catch (error) {
	console.log('No config.json found, using environment variables');
	config = {
		token: process.env.DISCORD_TOKEN,
		clientId: process.env.CLIENT_ID,
		guildId: process.env.GUILD_ID
	};
}

const { token } = config;

// Create a new client instance
const client = new Client({ intents: [GatewayIntentBits.Guilds] });

// Create a collection for commands
client.commands = new Collection();

// Load event handlers
const eventsPath = path.join(__dirname, 'events');
if (fs.existsSync(eventsPath)) {
	const eventFiles = fs.readdirSync(eventsPath).filter(file => file.endsWith('.js'));
	
	for (const file of eventFiles) {
		const filePath = path.join(eventsPath, file);
		const event = require(filePath);
		if (event.once) {
			client.once(event.name, (...args) => event.execute(...args));
		} else {
			client.on(event.name, (...args) => event.execute(...args));
		}
	}
}

// Read command files from the commands directory
const foldersPath = path.join(__dirname, 'commands');
const commandFolders = fs.readdirSync(foldersPath);

for (const folder of commandFolders) {
	// Grab all the command files from the commands directory you created earlier
	const commandsPath = path.join(foldersPath, folder);
	const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));
	
	// Grab the SlashCommandBuilder#toJSON() output of each command's data for deployment
	for (const file of commandFiles) {
		const filePath = path.join(commandsPath, file);
		const command = require(filePath);
		
		// Set a new item in the Collection with the key as the command name and the value as the exported module
		if ('data' in command && 'execute' in command) {
			client.commands.set(command.data.name, command);
		} else {
			console.log(`[WARNING] The command at ${filePath} is missing a required "data" or "execute" property.`);
		}
	}
}

// Handle slash command interactions
client.on(Events.InteractionCreate, async interaction => {
	if (!interaction.isChatInputCommand()) return;

	const command = interaction.client.commands.get(interaction.commandName);

	if (!command) {
		console.error(`No command matching ${interaction.commandName} was found.`);
		return;
	}

	try {
		await command.execute(interaction);
	} catch (error) {
		console.error(error);
		if (interaction.replied || interaction.deferred) {
			await interaction.followUp({ content: 'There was an error while executing this command!', ephemeral: true });
		} else {
			await interaction.reply({ content: 'There was an error while executing this command!', ephemeral: true });
		}
	}
});

// When the client is ready, run this code (only once).
// The ready event will be handled by events/ready.js if it exists
if (!fs.existsSync(path.join(__dirname, 'events'))) {
	client.once(Events.ClientReady, readyClient => {
		console.log(`Ready! Logged in as ${readyClient.user.tag}`);
	});
}

// Log in to Discord with your client's token
if (!token) {
	console.error('No bot token provided! Please check your config.json or environment variables.');
	process.exit(1);
}

client.login(token).catch(error => {
	console.error('Failed to login:', error);
	process.exit(1);
});