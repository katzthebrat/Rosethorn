const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
	data: new SlashCommandBuilder()
		.setName('serverinfo')
		.setDescription('Provides information about the server.'),
	async execute(interaction) {
		const { guild } = interaction;
		
		const serverInfoEmbed = new EmbedBuilder()
			.setTitle('Server Information')
			.setThumbnail(guild.iconURL())
			.addFields(
				{ name: 'Server Name', value: guild.name, inline: true },
				{ name: 'Total Members', value: guild.memberCount.toString(), inline: true },
				{ name: 'Created', value: `<t:${Math.floor(guild.createdTimestamp / 1000)}:F>`, inline: true },
				{ name: 'Owner', value: `<@${guild.ownerId}>`, inline: true },
				{ name: 'Server ID', value: guild.id, inline: true },
				{ name: 'Boost Level', value: guild.premiumTier.toString(), inline: true }
			)
			.setColor(0x0099FF)
			.setTimestamp();

		await interaction.reply({ embeds: [serverInfoEmbed] });
	},
};