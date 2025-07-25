import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from main import db, login_manager
from models import *
from utils.helpers import create_embed_dict, parse_duration

dashboard_bp = Blueprint('dashboard', __name__)

# Discord OAuth2 configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', 'your_discord_client_id')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', 'your_discord_client_secret')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/auth/callback')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@dashboard_bp.route('/')
def index():
    """Main dashboard page."""
    if not current_user.is_authenticated:
        return redirect(url_for('dashboard.login'))
    
    # Get user's guilds and bot statistics
    guilds = Guild.query.all()
    total_members = Member.query.count()
    total_commands = CustomCommand.query.count()
    active_tickets = Ticket.query.filter_by(status='open').count()
    
    # Recent activity
    recent_logs = BotLog.query.order_by(BotLog.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         guilds=guilds,
                         total_members=total_members,
                         total_commands=total_commands,
                         active_tickets=active_tickets,
                         recent_logs=recent_logs)

@dashboard_bp.route('/login')
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('login.html')

@dashboard_bp.route('/auth/discord')
def discord_auth():
    """Redirect to Discord OAuth2."""
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return redirect(discord_auth_url)

@dashboard_bp.route('/auth/callback')
def discord_callback():
    """Handle Discord OAuth2 callback."""
    code = request.args.get('code')
    if not code:
        flash('🥀 Authentication failed', 'error')
        return redirect(url_for('dashboard.login'))
    
    # Exchange code for token
    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
    }
    
    token_response = requests.post(
        'https://discord.com/api/oauth2/token',
        data=token_data
    )
    
    if token_response.status_code != 200:
        flash('🥀 Failed to authenticate with Discord', 'error')
        return redirect(url_for('dashboard.login'))
    
    token_json = token_response.json()
    access_token = token_json.get('access_token')
    
    # Get user info
    user_response = requests.get(
        'https://discord.com/api/users/@me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if user_response.status_code != 200:
        flash('🥀 Failed to get user information', 'error')
        return redirect(url_for('dashboard.login'))
    
    user_data = user_response.json()
    
    # Create or update user
    user = User.query.filter_by(discord_id=user_data['id']).first()
    if not user:
        user = User(
            discord_id=user_data['id'],
            username=user_data['username'],
            discriminator=user_data.get('discriminator'),
            avatar=user_data.get('avatar')
        )
        db.session.add(user)
    else:
        user.username = user_data['username']
        user.discriminator = user_data.get('discriminator')
        user.avatar = user_data.get('avatar')
        user.last_login = datetime.utcnow()
    
    db.session.commit()
    login_user(user)
    
    flash('🌹 Welcome to the Victorian Gothic Dashboard!', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('🌹 You have been gracefully logged out', 'info')
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/commands')
@login_required
def commands():
    """Command management page."""
    guild_id = request.args.get('guild_id')
    if not guild_id:
        guilds = Guild.query.all()
        return render_template('commands.html', guilds=guilds, commands=None, selected_guild=None)
    
    guild = Guild.query.filter_by(guild_id=guild_id).first()
    if not guild:
        flash('🥀 Guild not found', 'error')
        return redirect(url_for('dashboard.commands'))
    
    commands = CustomCommand.query.filter_by(guild_id=guild_id).order_by(CustomCommand.name).all()
    guilds = Guild.query.all()
    
    return render_template('commands.html', 
                         guilds=guilds, 
                         commands=commands, 
                         selected_guild=guild)

@dashboard_bp.route('/commands/create', methods=['POST'])
@login_required
def create_command():
    """Create a new custom command."""
    guild_id = request.form.get('guild_id')
    name = request.form.get('name', '').strip()
    trigger = request.form.get('trigger', '').strip()
    response = request.form.get('response', '').strip()
    embed = request.form.get('embed') == 'on'
    embed_title = request.form.get('embed_title', '').strip()
    embed_description = request.form.get('embed_description', '').strip()
    
    if not all([guild_id, name, trigger, response]):
        flash('🥀 Please fill in all required fields', 'error')
        return redirect(url_for('dashboard.commands', guild_id=guild_id))
    
    # Check if trigger already exists
    existing = CustomCommand.query.filter_by(guild_id=guild_id, trigger=trigger).first()
    if existing:
        flash('🥀 A command with that trigger already exists', 'error')
        return redirect(url_for('dashboard.commands', guild_id=guild_id))
    
    command = CustomCommand(
        guild_id=guild_id,
        name=name,
        trigger=trigger,
        response=response,
        embed=embed,
        embed_title=embed_title if embed_title else None,
        embed_description=embed_description if embed_description else None,
        created_by=current_user.discord_id
    )
    
    db.session.add(command)
    db.session.commit()
    
    flash(f'🌹 Command "{name}" created successfully!', 'success')
    return redirect(url_for('dashboard.commands', guild_id=guild_id))

@dashboard_bp.route('/commands/<int:command_id>/edit', methods=['POST'])
@login_required
def edit_command(command_id):
    """Edit an existing command."""
    command = CustomCommand.query.get_or_404(command_id)
    
    command.name = request.form.get('name', '').strip()
    command.trigger = request.form.get('trigger', '').strip()
    command.response = request.form.get('response', '').strip()
    command.embed = request.form.get('embed') == 'on'
    command.embed_title = request.form.get('embed_title', '').strip() or None
    command.embed_description = request.form.get('embed_description', '').strip() or None
    command.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'🌹 Command "{command.name}" updated successfully!', 'success')
    return redirect(url_for('dashboard.commands', guild_id=command.guild_id))

@dashboard_bp.route('/commands/<int:command_id>/delete', methods=['POST'])
@login_required
def delete_command(command_id):
    """Delete a command."""
    command = CustomCommand.query.get_or_404(command_id)
    guild_id = command.guild_id
    command_name = command.name
    
    db.session.delete(command)
    db.session.commit()
    
    flash(f'🥀 Command "{command_name}" deleted', 'info')
    return redirect(url_for('dashboard.commands', guild_id=guild_id))

@dashboard_bp.route('/tickets')
@login_required
def tickets():
    """Ticket management page."""
    guild_id = request.args.get('guild_id')
    status_filter = request.args.get('status', 'all')
    
    query = Ticket.query
    
    if guild_id:
        query = query.filter_by(guild_id=guild_id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    guilds = Guild.query.all()
    
    return render_template('tickets.html', 
                         tickets=tickets, 
                         guilds=guilds,
                         selected_guild_id=guild_id,
                         status_filter=status_filter)

@dashboard_bp.route('/economy')
@login_required
def economy():
    """Economy management page."""
    guild_id = request.args.get('guild_id')
    
    if not guild_id:
        guilds = Guild.query.all()
        return render_template('economy.html', guilds=guilds, guild=None, shop_items=None)
    
    guild = Guild.query.filter_by(guild_id=guild_id).first()
    if not guild:
        flash('🥀 Guild not found', 'error')
        return redirect(url_for('dashboard.economy'))
    
    shop_items = ShopItem.query.filter_by(guild_id=guild_id).order_by(ShopItem.category, ShopItem.name).all()
    top_earners = (Member.query.filter_by(guild_id=guild_id)
                   .order_by(Member.balance.desc())
                   .limit(10).all())
    
    guilds = Guild.query.all()
    
    return render_template('economy.html',
                         guilds=guilds,
                         guild=guild,
                         shop_items=shop_items,
                         top_earners=top_earners)

@dashboard_bp.route('/api/guild/<guild_id>/config', methods=['GET', 'POST'])
@login_required
def guild_config_api(guild_id):
    """API endpoint for guild configuration."""
    guild = Guild.query.filter_by(guild_id=guild_id).first()
    if not guild:
        return jsonify({'error': 'Guild not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'guild_id': guild.guild_id,
            'name': guild.name,
            'prefix': guild.prefix,
            'embed_color': guild.embed_color,
            'currency_name': guild.currency_name,
            'currency_symbol': guild.currency_symbol,
            'welcome_channel': guild.welcome_channel,
            'log_channel': guild.log_channel,
            'mod_role': guild.mod_role
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        
        guild.prefix = data.get('prefix', guild.prefix)
        guild.embed_color = data.get('embed_color', guild.embed_color)
        guild.currency_name = data.get('currency_name', guild.currency_name)
        guild.currency_symbol = data.get('currency_symbol', guild.currency_symbol)
        guild.welcome_channel = data.get('welcome_channel', guild.welcome_channel)
        guild.log_channel = data.get('log_channel', guild.log_channel)
        guild.mod_role = data.get('mod_role', guild.mod_role)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully!'})

@dashboard_bp.route('/api/commands/preview', methods=['POST'])
@login_required
def preview_command():
    """Preview a command before saving."""
    data = request.get_json()
    
    embed_dict = None
    if data.get('embed'):
        embed_dict = create_embed_dict(
            title=data.get('embed_title'),
            description=data.get('embed_description') or data.get('response'),
            color='#711417'
        )
    
    return jsonify({
        'success': True,
        'preview': {
            'response': data.get('response'),
            'embed': embed_dict
        }
    })

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Bot settings and configuration page."""
    guilds = Guild.query.all()
    return render_template('settings.html', guilds=guilds)

# Error handlers
@dashboard_bp.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message="The page you're looking for has vanished into the gothic mist."), 404

@dashboard_bp.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="The manor's spirits have encountered an unexpected disturbance."), 500
