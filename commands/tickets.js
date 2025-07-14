const { SlashCommandBuilder, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('tickets')
        .setDescription('Manage support tickets'),
    
    async execute(interaction) {
        // Create the embed
        const embed = new EmbedBuilder()
            .setColor(0x0099FF)
            .setTitle('🎟️ Support Ticket System')
            .setDescription('Please select the type of support ticket you need:')
            .addFields(
                { name: '🔐 Permissions', value: 'Issues related to permissions and access', inline: true },
                { name: '❓ General', value: 'General questions and support', inline: true },
                { name: '⚠️ Report', value: 'Report violations or issues', inline: true },
                { name: '🛡️ Defense Submission', value: 'Submit defense materials', inline: true }
            )
            .setFooter({ text: 'Click a button below to create your ticket' })
            .setTimestamp();

        // Create buttons
        const row = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder()
                    .setCustomId('ticket_permissions')
                    .setLabel('Permissions')
                    .setStyle(ButtonStyle.Primary)
                    .setEmoji('🔐'),
                new ButtonBuilder()
                    .setCustomId('ticket_general')
                    .setLabel('General')
                    .setStyle(ButtonStyle.Secondary)
                    .setEmoji('❓'),
                new ButtonBuilder()
                    .setCustomId('ticket_report')
                    .setLabel('Report')
                    .setStyle(ButtonStyle.Danger)
                    .setEmoji('⚠️'),
                new ButtonBuilder()
                    .setCustomId('ticket_defense')
                    .setLabel('Defense Submission')
                    .setStyle(ButtonStyle.Success)
                    .setEmoji('🛡️')
            );

        await interaction.reply({ embeds: [embed], components: [row] });
    },
};