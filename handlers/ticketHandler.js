const { 
    EmbedBuilder, 
    ActionRowBuilder, 
    ButtonBuilder, 
    ButtonStyle, 
    ChannelType, 
    PermissionFlagsBits,
    ModalBuilder,
    TextInputBuilder,
    TextInputStyle,
    AttachmentBuilder
} = require('discord.js');
const { ticketCategoryId, adminRoles = [] } = require('../config.json');
const fs = require('fs');

// Store ticket data
const tickets = new Map();

async function handleTicketButton(interaction) {
    // Handle ticket type selection
    if (interaction.customId.startsWith('ticket_')) {
        await createTicket(interaction);
    }
    // Handle admin buttons
    else if (interaction.customId === 'claim_ticket') {
        await claimTicket(interaction);
    }
    else if (interaction.customId === 'close_ticket') {
        await showCloseModal(interaction);
    }
}

async function createTicket(interaction) {
    const ticketType = interaction.customId.replace('ticket_', '');
    const user = interaction.user;
    const guild = interaction.guild;
    
    // Check if user already has an open ticket
    const existingTicket = Array.from(tickets.values()).find(
        ticket => ticket.userId === user.id && ticket.status === 'open'
    );
    
    if (existingTicket) {
        return await interaction.reply({
            content: `You already have an open ticket: <#${existingTicket.channelId}>`,
            ephemeral: true
        });
    }
    
    try {
        // Create ticket channel
        const ticketChannel = await guild.channels.create({
            name: `🎟️ | ${user.username}-${ticketType}`,
            type: ChannelType.GuildText,
            parent: ticketCategoryId,
            permissionOverwrites: [
                {
                    id: guild.id,
                    deny: [PermissionFlagsBits.ViewChannel],
                },
                {
                    id: user.id,
                    allow: [
                        PermissionFlagsBits.ViewChannel,
                        PermissionFlagsBits.SendMessages,
                        PermissionFlagsBits.ReadMessageHistory
                    ],
                },
                // Add permissions for admin roles (you may need to adjust these role IDs)
                // {
                //     id: 'ADMIN_ROLE_ID',
                //     allow: [
                //         PermissionFlagsBits.ViewChannel,
                //         PermissionFlagsBits.SendMessages,
                //         PermissionFlagsBits.ReadMessageHistory
                //     ],
                // }
            ]
        });
        
        // Store ticket data
        const ticketData = {
            channelId: ticketChannel.id,
            userId: user.id,
            username: user.username,
            type: ticketType,
            status: 'open',
            createdAt: new Date(),
            claimedBy: null,
            messages: []
        };
        tickets.set(ticketChannel.id, ticketData);
        
        // Create initial embed asking for user details
        const initialEmbed = new EmbedBuilder()
            .setColor(0x00FF00)
            .setTitle(`🎟️ New ${capitalizeFirst(ticketType)} Ticket`)
            .setDescription('Thank you for creating a support ticket. Please provide the following information:')
            .addFields(
                { name: '📝 Required Information', value: '• **Preferred Name:** Your preferred name\n• **Gamertag:** Your gaming username\n• **Issue:** Detailed description of your issue', inline: false }
            )
            .setFooter({ text: `Ticket opened by ${user.username}` })
            .setTimestamp();
        
        // Create admin buttons
        const adminRow = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder()
                    .setCustomId('claim_ticket')
                    .setLabel('Claim')
                    .setStyle(ButtonStyle.Primary)
                    .setEmoji('✋'),
                new ButtonBuilder()
                    .setCustomId('close_ticket')
                    .setLabel('Close')
                    .setStyle(ButtonStyle.Danger)
                    .setEmoji('🔒')
            );
        
        // Send initial message with admin controls
        await ticketChannel.send({
            content: `${user} Welcome to your support ticket!\n\n🔔 **Admin Staff** - Please assist this user.`,
            embeds: [initialEmbed],
            components: [adminRow]
        });
        
        // Reply to the interaction
        await interaction.reply({
            content: `Your ${ticketType} ticket has been created! Please check <#${ticketChannel.id}>`,
            ephemeral: true
        });
        
    } catch (error) {
        console.error('Error creating ticket:', error);
        await interaction.reply({
            content: 'There was an error creating your ticket. Please try again later.',
            ephemeral: true
        });
    }
}

async function claimTicket(interaction) {
    const channelId = interaction.channel.id;
    const ticket = tickets.get(channelId);
    
    if (!ticket) {
        return await interaction.reply({
            content: 'This is not a valid ticket channel.',
            ephemeral: true
        });
    }
    
    // Check if user has admin permissions
    if (!isAdmin(interaction.member)) {
        return await interaction.reply({
            content: 'Only admin staff can claim tickets.',
            ephemeral: true
        });
    }
    
    if (ticket.claimedBy) {
        return await interaction.reply({
            content: `This ticket has already been claimed by <@${ticket.claimedBy}>.`,
            ephemeral: true
        });
    }
    
    // Update ticket data
    ticket.claimedBy = interaction.user.id;
    ticket.claimedAt = new Date();
    tickets.set(channelId, ticket);
    
    // Create claim embed
    const claimEmbed = new EmbedBuilder()
        .setColor(0xFFFF00)
        .setTitle('🎟️ Ticket Claimed')
        .setDescription(`This ticket has been claimed by ${interaction.user}`)
        .setTimestamp();
    
    await interaction.reply({ embeds: [claimEmbed] });
}

async function showCloseModal(interaction) {
    // Check if user has admin permissions
    if (!isAdmin(interaction.member)) {
        return await interaction.reply({
            content: 'Only admin staff can close tickets.',
            ephemeral: true
        });
    }
    
    const modal = new ModalBuilder()
        .setCustomId('close_ticket_modal')
        .setTitle('Close Ticket');
    
    const resolutionInput = new TextInputBuilder()
        .setCustomId('resolution')
        .setLabel('How was this issue resolved?')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('Please describe how the issue was resolved...')
        .setRequired(true)
        .setMaxLength(1000);
    
    const firstActionRow = new ActionRowBuilder().addComponents(resolutionInput);
    modal.addComponents(firstActionRow);
    
    await interaction.showModal(modal);
}

async function handleModalSubmit(interaction) {
    if (interaction.customId === 'close_ticket_modal') {
        await closeTicket(interaction);
    }
}

async function closeTicket(interaction) {
    const channelId = interaction.channel.id;
    const ticket = tickets.get(channelId);
    
    if (!ticket) {
        return await interaction.reply({
            content: 'This is not a valid ticket channel.',
            ephemeral: true
        });
    }
    
    const resolution = interaction.fields.getTextInputValue('resolution');
    
    // Update ticket data
    ticket.status = 'closed';
    ticket.closedBy = interaction.user.id;
    ticket.closedAt = new Date();
    ticket.resolution = resolution;
    tickets.set(channelId, ticket);
    
    // Create closure summary embed
    const summaryEmbed = new EmbedBuilder()
        .setColor(0xFF0000)
        .setTitle('🎟️ **CLOSED** - Ticket Summary')
        .addFields(
            { name: '👤 Opened by', value: `<@${ticket.userId}>`, inline: true },
            { name: '✋ Claimed by', value: ticket.claimedBy ? `<@${ticket.claimedBy}>` : 'Not claimed', inline: true },
            { name: '🔒 Closed by', value: `<@${ticket.closedBy}>`, inline: true },
            { name: '📝 Type', value: capitalizeFirst(ticket.type), inline: true },
            { name: '⏰ Duration', value: calculateDuration(ticket.createdAt, ticket.closedAt), inline: true },
            { name: '✅ Resolution', value: resolution, inline: false }
        )
        .setFooter({ text: '**CLOSED**' })
        .setTimestamp();
    
    // Generate transcript
    const transcript = await generateTranscript(interaction.channel, ticket);
    
    try {
        // Send summary and transcript
        await interaction.reply({
            embeds: [summaryEmbed],
            files: [transcript]
        });
        
        // Wait a bit then archive/delete the channel
        setTimeout(async () => {
            try {
                await interaction.channel.delete();
                tickets.delete(channelId);
            } catch (error) {
                console.error('Error deleting ticket channel:', error);
            }
        }, 10000); // 10 seconds delay
        
    } catch (error) {
        console.error('Error closing ticket:', error);
        await interaction.reply({
            content: 'Error closing ticket. Please try again.',
            ephemeral: true
        });
    }
}

async function generateTranscript(channel, ticket) {
    const messages = await channel.messages.fetch({ limit: 100 });
    const sortedMessages = messages.sort((a, b) => a.createdTimestamp - b.createdTimestamp);
    
    let transcript = `Ticket Transcript\n`;
    transcript += `================\n`;
    transcript += `Channel: #${channel.name}\n`;
    transcript += `Opened by: ${ticket.username} (${ticket.userId})\n`;
    transcript += `Type: ${ticket.type}\n`;
    transcript += `Created: ${ticket.createdAt.toISOString()}\n`;
    transcript += `Closed: ${ticket.closedAt.toISOString()}\n`;
    transcript += `Resolution: ${ticket.resolution}\n`;
    transcript += `================\n\n`;
    
    sortedMessages.forEach(message => {
        const timestamp = message.createdAt.toISOString();
        const author = message.author.username;
        const content = message.content || '[No content]';
        transcript += `[${timestamp}] ${author}: ${content}\n`;
        
        if (message.embeds.length > 0) {
            transcript += `  └─ [Embed: ${message.embeds[0].title || 'Untitled'}]\n`;
        }
        
        if (message.attachments.size > 0) {
            message.attachments.forEach(attachment => {
                transcript += `  └─ [Attachment: ${attachment.name}]\n`;
            });
        }
    });
    
    return new AttachmentBuilder(Buffer.from(transcript, 'utf-8'), {
        name: `ticket-${ticket.type}-${ticket.userId}-${Date.now()}.txt`
    });
}

function isAdmin(member) {
    // Check if member has administrator permission
    if (member.permissions.has(PermissionFlagsBits.Administrator)) {
        return true;
    }
    
    // Check if member has any of the configured admin roles
    return member.roles.cache.some(role => adminRoles.includes(role.name));
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function calculateDuration(start, end) {
    const diff = end - start;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

module.exports = {
    handleTicketButton,
    handleModalSubmit,
    tickets
};