const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
	data: new SlashCommandBuilder()
		.setName('userinfo')
		.setDescription('Provides information about a user.')
		.addUserOption(option =>
			option.setName('target')
				.setDescription('The user to get information about')
				.setRequired(false)),
	async execute(interaction) {
		const user = interaction.options.getUser('target') || interaction.user;
		const member = interaction.guild.members.cache.get(user.id);
		
		const userInfoEmbed = new EmbedBuilder()
			.setTitle('User Information')
			.setThumbnail(user.displayAvatarURL())
			.addFields(
				{ name: 'Username', value: user.username, inline: true },
				{ name: 'Display Name', value: member ? member.displayName : 'N/A', inline: true },
				{ name: 'ID', value: user.id, inline: true },
				{ name: 'Account Created', value: `<t:${Math.floor(user.createdTimestamp / 1000)}:F>`, inline: true },
				{ name: 'Joined Server', value: member ? `<t:${Math.floor(member.joinedTimestamp / 1000)}:F>` : 'N/A', inline: true },
				{ name: 'Bot', value: user.bot ? 'Yes' : 'No', inline: true }
			)
			.setColor(member ? member.displayHexColor : 0x0099FF)
			.setTimestamp();

		await interaction.reply({ embeds: [userInfoEmbed] });
	},
};