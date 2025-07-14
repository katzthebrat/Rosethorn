const { SlashCommandBuilder } = require('discord.js');

module.exports = {
	data: new SlashCommandBuilder()
		.setName('ping')
		.setDescription('Replies with Pong!'),
	async execute(interaction) {
		const sent = await interaction.reply({ content: 'Pinging...', fetchReply: true });
		const timeDiff = sent.createdTimestamp - interaction.createdTimestamp;
		await interaction.editReply(`Pong! Bot latency: ${timeDiff}ms, API latency: ${Math.round(interaction.client.ws.ping)}ms`);
	},
};