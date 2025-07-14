# 🌹 Onboarding System Documentation

The Rosethorn Discord bot includes a comprehensive member onboarding system that automates the process of welcoming new members and collecting their information for server administrators.

## ✨ Features

### 1. Automatic Welcome Process
- **Instant Detection**: Bot automatically detects when new members join the server
- **Private Messaging**: Sends a welcoming direct message to new members
- **Interactive Form**: Provides a button to trigger a registration modal

### 2. Member Information Collection
The onboarding form collects:
- **Preferred Name**: What the member would like to be called
- **Gamertag**: Their gaming username/identifier
- **Birthday**: Day, Month, and Year (with validation)

### 3. Admin Review System
- **Notification Channel**: Sends detailed member information to the configured admin channel
- **Role Mention**: Alerts the specified admin role about new registrations
- **Rich Embeds**: Displays member avatar, join date, account age, and submitted information

### 4. Admin Actions
Three action buttons for administrators:
- **❌ Deny**: Rejects the member registration
- **✅ Approve**: Approves the member and sets their nickname
- **🔞 18+**: Approves with 18+ designation

### 5. Automated Member Management
- **Nickname Setting**: Automatically sets approved members' nicknames to "Preferred Name [Gamertag]"
- **Status Updates**: Updates the embed with approval status and acting administrator
- **Member Notifications**: Sends confirmation messages to approved/denied members

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Onboarding system configuration
ONBOARDING_CHANNEL_ID=1311529665348767835
ONBOARDING_ROLE_ID=1308905911489921124
```

### Required Bot Permissions

The bot needs these permissions:
- **Send Messages**: To send embeds and notifications
- **Send Messages in DMs**: To send registration forms to new members
- **Manage Nicknames**: To change member nicknames upon approval
- **Use External Emojis**: For button emojis (optional)
- **View Channel History**: To edit embed messages

### Required Intents

The bot automatically enables:
- **Members Intent**: To detect member join events
- **Message Content Intent**: For existing command functionality
- **Guilds Intent**: For guild access

## 🚀 How It Works

### 1. Member Joins Server
```
New Member → Bot Detects Join → Sends Welcome DM
```

### 2. Registration Process
```
Member → Clicks "Complete Registration" → Fills Modal Form → Submits
```

### 3. Admin Review
```
Form Submitted → Admin Channel Notification → Admin Reviews → Takes Action
```

### 4. Approval Process
```
Admin Clicks Button → Member Nickname Updated → Status Updated → Member Notified
```

## 📋 Form Validation

The system includes comprehensive validation:

### Birthday Validation
- **Day**: Must be 1-31
- **Month**: Must be 1-12  
- **Year**: Must be 1900-2024
- **Format**: Automatically formatted as DD/MM/YYYY

### Input Limits
- **Preferred Name**: Maximum 50 characters
- **Gamertag**: Maximum 50 characters
- **Birthday Fields**: Appropriate character limits for dates

## 🛡️ Error Handling

### Graceful Fallbacks
- **DMs Disabled**: Falls back to system channel notification if member has DMs disabled
- **Permission Errors**: Provides clear error messages for missing permissions
- **Invalid Input**: User-friendly validation error messages
- **Network Issues**: Comprehensive logging for troubleshooting

### Logging
All onboarding events are logged including:
- Member join events
- Form submissions
- Admin actions
- Error conditions

## 🎨 Customization

### Embed Colors
- **New Registration**: Blue (`discord.Color.blue()`)
- **Approved**: Green (`discord.Color.green()`)
- **Denied**: Red (`discord.Color.red()`)
- **18+ Approved**: Purple (`discord.Color.purple()`)

### Button Styles
- **Deny**: Danger (Red)
- **Approve**: Success (Green)
- **18+**: Secondary (Gray)

## 🔧 Maintenance

### Monitoring
- Check bot logs for join events and errors
- Monitor the admin channel for pending registrations
- Verify bot has required permissions

### Troubleshooting

**Members not receiving DMs:**
- Check if bot has DM permissions
- Verify member hasn't blocked the bot
- Check system channel fallback messages

**Admin buttons not working:**
- Verify bot has Manage Nicknames permission
- Check role hierarchy (bot role must be higher than member roles)
- Review error logs for permission issues

**Missing notifications:**
- Verify channel ID in configuration
- Check if bot has access to the admin channel
- Ensure role ID is correct for mentions

## 📈 Usage Statistics

The system automatically tracks:
- Member join events
- Form completion rates
- Admin action distribution
- Error occurrences

This information is available in the bot logs for analysis.

## 🔄 Integration

The onboarding system integrates seamlessly with the existing Rosethorn bot:
- **No interference** with existing commands
- **Modular design** allows easy modification
- **Persistent views** survive bot restarts
- **Maintains** all existing bot functionality

## 📞 Support

For issues or questions about the onboarding system:
1. Check the bot logs for error messages
2. Verify configuration settings
3. Ensure bot permissions are correct
4. Review this documentation for troubleshooting steps

The onboarding system is designed to be robust and user-friendly while providing administrators with the tools they need to manage new members effectively.