"""
Utility functions for the Rosethorn Discord Bot.
"""
import random
import discord
from datetime import datetime
from typing import List, Optional

def format_role_list(roles: List[discord.Role]) -> str:
    """Format a list of roles for display."""
    if not roles:
        return "No roles found"
    
    role_names = [role.name for role in roles if role.name != "@everyone"]
    return ", ".join(role_names) if role_names else "No custom roles"

def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a standardized embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    return embed

def roll_dice(sides: int = 6, count: int = 1) -> List[int]:
    """Roll dice and return results."""
    if sides < 2 or sides > 100:
        raise ValueError("Dice must have between 2 and 100 sides")
    if count < 1 or count > 10:
        raise ValueError("Must roll between 1 and 10 dice")
    
    return [random.randint(1, sides) for _ in range(count)]

def magic_8ball() -> str:
    """Get a magic 8-ball response."""
    responses = [
        "It is certain",
        "It is decidedly so", 
        "Without a doubt",
        "Yes definitely",
        "You may rely on it",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes",
        "Reply hazy, try again",
        "Ask again later",
        "Better not tell you now",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "My reply is no",
        "My sources say no",
        "Outlook not so good",
        "Very doubtful"
    ]
    return random.choice(responses)

def validate_user_permissions(member: discord.Member, required_permissions: List[str]) -> bool:
    """Check if a member has required permissions."""
    permissions = member.guild_permissions
    
    permission_map = {
        'manage_roles': permissions.manage_roles,
        'manage_channels': permissions.manage_channels,
        'kick_members': permissions.kick_members,
        'manage_messages': permissions.manage_messages,
        'timeout_members': permissions.moderate_members,
        'use_voice': permissions.use_voice_activation,
        'stream': permissions.stream
    }
    
    return all(permission_map.get(perm, False) for perm in required_permissions)

def get_member_top_role(member: discord.Member) -> Optional[discord.Role]:
    """Get the highest role of a member (excluding @everyone)."""
    roles = [role for role in member.roles if role.name != "@everyone"]
    return max(roles, key=lambda x: x.position) if roles else None