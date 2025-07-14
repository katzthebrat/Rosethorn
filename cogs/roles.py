"""
Role management commands for the Rosethorn Discord Bot.
"""
import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, format_role_list, validate_user_permissions
from config import ROLE_PERMISSIONS

class RoleManagement(commands.Cog):
    """Cog for managing Discord server roles."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createrole", description="Create a new role")
    @app_commands.describe(
        name="The name of the role to create",
        color="The color of the role (hex format, e.g., #FF0000)",
        reason="Reason for creating the role"
    )
    async def create_role(self, interaction: discord.Interaction, name: str, color: str = None, reason: str = None):
        """Create a new role in the server."""
        if not interaction.user.guild_permissions.manage_roles:
            embed = create_embed(
                "Permission Denied", 
                "You don't have permission to manage roles.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            role_color = discord.Color.default()
            if color:
                # Remove # if present and convert to int
                color_hex = color.lstrip('#')
                role_color = discord.Color(int(color_hex, 16))
        except ValueError:
            embed = create_embed(
                "Invalid Color",
                "Please provide a valid hex color (e.g., #FF0000)",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            role = await interaction.guild.create_role(
                name=name,
                color=role_color,
                reason=reason or f"Role created by {interaction.user}"
            )
            
            embed = create_embed(
                "Role Created",
                f"Successfully created role **{role.name}** with color {role.color}",
                discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = create_embed(
                "Permission Error",
                "I don't have permission to create roles. Please check my permissions.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_embed(
                "Error",
                f"Failed to create role: {str(e)}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="assignrole", description="Assign a role to a user")
    @app_commands.describe(
        user="The user to assign the role to",
        role="The role to assign"
    )
    async def assign_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Assign a role to a user."""
        if not interaction.user.guild_permissions.manage_roles:
            embed = create_embed(
                "Permission Denied",
                "You don't have permission to manage roles.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            embed = create_embed(
                "Permission Denied",
                "You cannot assign a role that is higher than or equal to your highest role.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            if role in user.roles:
                embed = create_embed(
                    "Role Already Assigned",
                    f"{user.mention} already has the role **{role.name}**",
                    discord.Color.yellow()
                )
            else:
                await user.add_roles(role, reason=f"Role assigned by {interaction.user}")
                embed = create_embed(
                    "Role Assigned",
                    f"Successfully assigned **{role.name}** to {user.mention}",
                    discord.Color.green()
                )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = create_embed(
                "Permission Error",
                "I don't have permission to assign this role. Please check my permissions.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_embed(
                "Error",
                f"Failed to assign role: {str(e)}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="removerole", description="Remove a role from a user")
    @app_commands.describe(
        user="The user to remove the role from",
        role="The role to remove"
    )
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Remove a role from a user."""
        if not interaction.user.guild_permissions.manage_roles:
            embed = create_embed(
                "Permission Denied",
                "You don't have permission to manage roles.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            if role not in user.roles:
                embed = create_embed(
                    "Role Not Found",
                    f"{user.mention} doesn't have the role **{role.name}**",
                    discord.Color.yellow()
                )
            else:
                await user.remove_roles(role, reason=f"Role removed by {interaction.user}")
                embed = create_embed(
                    "Role Removed",
                    f"Successfully removed **{role.name}** from {user.mention}",
                    discord.Color.green()
                )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = create_embed(
                "Permission Error",
                "I don't have permission to remove this role. Please check my permissions.",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_embed(
                "Error",
                f"Failed to remove role: {str(e)}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="listroles", description="List all roles in the server")
    async def list_roles(self, interaction: discord.Interaction):
        """List all roles in the server."""
        roles = [role for role in interaction.guild.roles if role.name != "@everyone"]
        roles.sort(key=lambda x: x.position, reverse=True)
        
        if not roles:
            embed = create_embed(
                "Server Roles",
                "No custom roles found in this server.",
                discord.Color.blue()
            )
        else:
            role_list = []
            for role in roles:
                member_count = len(role.members)
                role_list.append(f"**{role.name}** - {member_count} members")
            
            embed = create_embed(
                "Server Roles",
                "\n".join(role_list),
                discord.Color.blue()
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userroles", description="Show roles of a specific user")
    @app_commands.describe(user="The user to check roles for")
    async def user_roles(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show roles of a specific user."""
        target_user = user or interaction.user
        
        user_roles = [role for role in target_user.roles if role.name != "@everyone"]
        user_roles.sort(key=lambda x: x.position, reverse=True)
        
        embed = create_embed(
            f"Roles for {target_user.display_name}",
            format_role_list(user_roles),
            discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(RoleManagement(bot))