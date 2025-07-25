import discord
import aiohttp
import json
from datetime import datetime
import config

def get_discord_user_info(discord_id):
    """Get Discord user information"""
    # This would typically use Discord API
    return {
        'id': discord_id,
        'username': 'User',
        'discriminator': '0001',
        'avatar': None
    }

def verify_guild_access(user_id, guild_id):
    """Verify user has access to manage guild"""
    # Implement guild access verification
    return True

def create_embed_preview(embed_data):
    """Create HTML preview of Discord embed"""
    if not embed_data:
        return '<div class="embed-preview">No embed data</div>'
    
    title = embed_data.get('title', '')
    description = embed_data.get('description', '')
    color = embed_data.get('color', config.EMBED_COLOR)
    
    # Convert color to hex if it's an integer
    if isinstance(color, int):
        color = f"#{color:06x}"
    elif not color.startswith('#'):
        color = f"#{color}"
    
    fields_html = ''
    if 'fields' in embed_data:
        for field in embed_data['fields']:
            inline_class = 'inline' if field.get('inline', False) else ''
            fields_html += f'''
                <div class="embed-field {inline_class}">
                    <div class="field-name">{field.get('name', '')}</div>
                    <div class="field-value">{field.get('value', '')}</div>
                </div>
            '''
    
    footer_html = ''
    if 'footer' in embed_data:
        footer_html = f'<div class="embed-footer">{embed_data["footer"].get("text", "")}</div>'
    
    thumbnail_html = ''
    if 'thumbnail' in embed_data:
        thumbnail_html = f'<img src="{embed_data["thumbnail"].get("url", "")}" class="embed-thumbnail" alt="Thumbnail">'
    
    return f'''
        <div class="embed-preview" style="border-left: 4px solid {color};">
            {thumbnail_html}
            <div class="embed-content">
                {f'<div class="embed-title">{title}</div>' if title else ''}
                {f'<div class="embed-description">{description}</div>' if description else ''}
                {fields_html}
                {footer_html}
            </div>
        </div>
    '''

def format_currency(amount, symbol="🌹"):
    """Format currency amount with symbol"""
    return f"{symbol} {amount:,.2f}"

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "Never"
    return dt.strftime("%Y-%m-%d %H:%M UTC")

def get_user_level(xp):
    """Calculate user level from XP"""
    # Simple level calculation: level = sqrt(xp / 100)
    import math
    return int(math.sqrt(xp / 100)) + 1

def xp_for_level(level):
    """Calculate XP required for level"""
    return (level - 1) ** 2 * 100

def validate_embed_data(data):
    """Validate embed data structure"""
    if not isinstance(data, dict):
        return False
    
    # Check required fields exist and are valid types
    valid_keys = ['title', 'description', 'color', 'fields', 'footer', 'thumbnail', 'image']
    
    for key, value in data.items():
        if key not in valid_keys:
            return False
        
        if key == 'fields' and not isinstance(value, list):
            return False
        elif key in ['footer', 'thumbnail', 'image'] and not isinstance(value, dict):
            return False
    
    return True

def create_error_embed(title, message):
    """Create standardized error embed data"""
    return {
        'title': f"❌ {title}",
        'description': message,
        'color': 0xFF6B6B,
        'footer': {'text': '🕯️ RosethornBot - Gothic Error Handling'}
    }

def create_success_embed(title, message):
    """Create standardized success embed data"""
    return {
        'title': f"✅ {title}",
        'description': message,
        'color': config.EMBED_COLOR,
        'footer': {'text': '🌹 RosethornBot - Victorian Excellence'}
    }

def sanitize_input(text, max_length=2000):
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<script>', '</script>', '<iframe>', '</iframe>']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Limit length
    return text[:max_length]

def parse_duration(duration_str):
    """Parse duration string like '1d', '2h', '30m' to timedelta"""
    import re
    from datetime import timedelta
    
    pattern = r'(\d+)([dhms])'
    matches = re.findall(pattern, duration_str.lower())
    
    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        if unit == 'd':
            total_seconds += amount * 86400
        elif unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 's':
            total_seconds += amount
    
    return timedelta(seconds=total_seconds)

def format_duration(td):
    """Format timedelta to human readable string"""
    if not td:
        return "0 seconds"
    
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds and not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ", ".join(parts)

def get_gothic_emoji(category="general"):
    """Get random Gothic emoji for category"""
    import random
    
    emojis = {
        "general": ["🌹", "🥀", "🕯️", "🌙", "⭐", "🗝️"],
        "success": ["✨", "🌹", "👑", "💎"],
        "error": ["💀", "⚰️", "🖤", "🌚"],
        "warning": ["⚠️", "🚨", "🔥", "⚡"],
        "info": ["📜", "📖", "🔍", "💭"]
    }
    
    return random.choice(emojis.get(category, emojis["general"]))
