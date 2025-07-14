const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
	data: new SlashCommandBuilder()
		.setName('help')
		.setDescription('Shows information about available commands.'),
	async execute(interaction) {
		const helpEmbed = new EmbedBuilder()
			.setTitle('🌹 Rosethorn Bot Commands')
			.setDescription('Here are all the available slash commands:')
			.addFields(
				{ 
					name: '🛠️ Utility Commands', 
					value: '`/ping` - Check bot latency and response time\n`/help` - Show this help message', 
					inline: false 
				},
				{ 
					name: 'ℹ️ Information Commands', 
					value: '`/serverinfo` - Display server information\n`/userinfo [user]` - Show user information', 
					inline: false 
				},
				{ 
					name: '🎉 Fun Commands', 
					value: '`/echo <text>` - Echo back your message', 
					inline: false 
				}
			)
			.setColor(0xFF69B4)
			.setFooter({ 
				text: 'Use /command to execute any command', 
				iconURL: interaction.client.user.displayAvatarURL() 
			})
			.setTimestamp();

		await interaction.reply({ embeds: [helpEmbed] });
	},
};