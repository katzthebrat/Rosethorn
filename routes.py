from flask import render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime, timedelta
import config
from models import User, GuildConfig, Command, Ticket, Application, CheckIn, ShopItem, SocialMonitor
from utils import get_discord_user_info, verify_guild_access, create_embed_preview
import logging

logger = logging.getLogger(__name__)

def setup_routes(app, db):
    """Setup all Flask routes"""
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return render_template('dashboard.html', user=current_user)
    
    @app.route('/login')
    def login():
        """Login page"""
        return render_template('login.html')
    
    @app.route('/auth/discord')
    def discord_auth():
        """Discord OAuth authentication"""
        # In a real implementation, this would handle Discord OAuth
        # For now, we'll simulate with a test user
        discord_id = request.args.get('discord_id', '123456789')
        username = request.args.get('username', 'TestUser')
        
        user = User.query.filter_by(discord_id=discord_id).first()
        if not user:
            user = User(
                discord_id=discord_id,
                username=username,
                discriminator='0001'
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout user"""
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard"""
        # Get user's guilds (simplified)
        guilds = GuildConfig.query.all()
        
        # Get recent activity
        recent_commands = Command.query.order_by(Command.updated_at.desc()).limit(10).all()
        recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(5).all()
        
        stats = {
            'total_commands': Command.query.count(),
            'total_tickets': Ticket.query.count(),
            'active_monitors': SocialMonitor.query.filter_by(enabled=True).count(),
            'total_users': User.query.count()
        }
        
        return render_template('dashboard.html', 
                             guilds=guilds, 
                             recent_commands=recent_commands,
                             recent_tickets=recent_tickets,
                             stats=stats)
    
    @app.route('/commands')
    @login_required
    def commands():
        """Command management page"""
        guild_id = request.args.get('guild_id')
        if not guild_id:
            flash('Please select a guild first.', 'error')
            return redirect(url_for('dashboard'))
        
        commands = Command.query.filter_by(guild_id=guild_id).all()
        guild = GuildConfig.query.filter_by(guild_id=guild_id).first()
        
        return render_template('commands.html', commands=commands, guild=guild)
    
    @app.route('/api/commands', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @login_required
    def api_commands():
        """Command management API"""
        if request.method == 'GET':
            guild_id = request.args.get('guild_id')
            commands = Command.query.filter_by(guild_id=guild_id).all()
            return jsonify([{
                'id': cmd.id,
                'name': cmd.name,
                'content': cmd.content,
                'embed_data': cmd.embed_data,
                'uses': cmd.uses,
                'enabled': cmd.enabled,
                'created_at': cmd.created_at.isoformat(),
                'updated_at': cmd.updated_at.isoformat()
            } for cmd in commands])
        
        elif request.method == 'POST':
            data = request.get_json()
            command = Command(
                guild_id=data['guild_id'],
                name=data['name'],
                content=data['content'],
                embed_data=data.get('embed_data'),
                created_by=current_user.discord_id
            )
            db.session.add(command)
            db.session.commit()
            
            return jsonify({
                'id': command.id,
                'message': 'Command created successfully! 🌹',
                'success': True
            })
        
        elif request.method == 'PUT':
            command_id = request.args.get('id')
            data = request.get_json()
            
            command = Command.query.get(command_id)
            if not command:
                return jsonify({'error': 'Command not found', 'success': False}), 404
            
            command.name = data.get('name', command.name)
            command.content = data.get('content', command.content)
            command.embed_data = data.get('embed_data', command.embed_data)
            command.enabled = data.get('enabled', command.enabled)
            command.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'message': 'Command updated with Victorian elegance! ✨',
                'success': True
            })
        
        elif request.method == 'DELETE':
            command_id = request.args.get('id')
            command = Command.query.get(command_id)
            
            if not command:
                return jsonify({'error': 'Command not found', 'success': False}), 404
            
            db.session.delete(command)
            db.session.commit()
            
            return jsonify({
                'message': 'Command deleted from our Gothic archives 🥀',
                'success': True
            })
    
    @app.route('/api/embed-preview', methods=['POST'])
    @login_required
    def embed_preview():
        """Generate embed preview"""
        data = request.get_json()
        preview_html = create_embed_preview(data)
        return jsonify({'html': preview_html, 'success': True})
    
    @app.route('/tickets')
    @login_required
    def tickets():
        """Ticket management page"""
        guild_id = request.args.get('guild_id')
        if not guild_id:
            flash('Please select a guild first.', 'error')
            return redirect(url_for('dashboard'))
        
        tickets = Ticket.query.filter_by(guild_id=guild_id).order_by(Ticket.created_at.desc()).all()
        guild = GuildConfig.query.filter_by(guild_id=guild_id).first()
        
        return render_template('tickets.html', tickets=tickets, guild=guild)
    
    @app.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
    @login_required
    def update_ticket_status():
        """Update ticket status"""
        ticket_id = request.view_args['ticket_id']
        data = request.get_json()
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found', 'success': False}), 404
        
        ticket.status = data['status']
        if data['status'] == 'closed':
            ticket.closed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Ticket status updated to {data["status"]} 🎫',
            'success': True
        })
    
    @app.route('/economy')
    @login_required
    def economy():
        """Economy management page"""
        guild_id = request.args.get('guild_id')
        if not guild_id:
            flash('Please select a guild first.', 'error')
            return redirect(url_for('dashboard'))
        
        guild = GuildConfig.query.filter_by(guild_id=guild_id).first()
        shop_items = ShopItem.query.filter_by(guild_id=guild_id).all()
        
        # Get economy stats
        total_currency = db.session.query(db.func.sum(User.currency)).scalar() or 0
        total_transactions = db.session.query(db.func.count(CheckIn.id)).scalar() or 0
        
        stats = {
            'total_currency': total_currency,
            'total_transactions': total_transactions,
            'total_items': len(shop_items),
            'active_items': len([item for item in shop_items if item.enabled])
        }
        
        return render_template('economy.html', 
                             guild=guild, 
                             shop_items=shop_items, 
                             stats=stats)
    
    @app.route('/api/shop-items', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @login_required
    def api_shop_items():
        """Shop item management API"""
        if request.method == 'GET':
            guild_id = request.args.get('guild_id')
            items = ShopItem.query.filter_by(guild_id=guild_id).all()
            return jsonify([{
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'category': item.category,
                'rarity': item.rarity,
                'stock': item.stock,
                'enabled': item.enabled
            } for item in items])
        
        elif request.method == 'POST':
            data = request.get_json()
            item = ShopItem(
                guild_id=data['guild_id'],
                name=data['name'],
                description=data['description'],
                price=data['price'],
                category=data.get('category', 'misc'),
                rarity=data.get('rarity', 'common'),
                stock=data.get('stock', -1)
            )
            db.session.add(item)
            db.session.commit()
            
            return jsonify({
                'id': item.id,
                'message': 'Item added to the Gothic marketplace! 🏪',
                'success': True
            })
    
    @app.route('/social')
    @login_required
    def social():
        """Social media monitoring page"""
        guild_id = request.args.get('guild_id')
        if not guild_id:
            flash('Please select a guild first.', 'error')
            return redirect(url_for('dashboard'))
        
        monitors = SocialMonitor.query.filter_by(guild_id=guild_id).all()
        guild = GuildConfig.query.filter_by(guild_id=guild_id).first()
        
        return render_template('social.html', monitors=monitors, guild=guild)
    
    @app.route('/api/social-monitors', methods=['GET', 'POST', 'DELETE'])
    @login_required
    def api_social_monitors():
        """Social media monitor management API"""
        if request.method == 'GET':
            guild_id = request.args.get('guild_id')
            monitors = SocialMonitor.query.filter_by(guild_id=guild_id).all()
            return jsonify([{
                'id': monitor.id,
                'platform': monitor.platform,
                'username': monitor.username,
                'channel_id': monitor.channel_id,
                'enabled': monitor.enabled,
                'created_at': monitor.created_at.isoformat()
            } for monitor in monitors])
        
        elif request.method == 'POST':
            data = request.get_json()
            monitor = SocialMonitor(
                guild_id=data['guild_id'],
                platform=data['platform'],
                username=data['username'],
                channel_id=data['channel_id']
            )
            db.session.add(monitor)
            db.session.commit()
            
            return jsonify({
                'id': monitor.id,
                'message': 'Social media monitor added! 📱',
                'success': True
            })
    
    @app.route('/analytics')
    @login_required
    def analytics():
        """Analytics dashboard"""
        guild_id = request.args.get('guild_id')
        
        # Get various analytics
        command_usage = db.session.query(
            Command.name, 
            db.func.sum(Command.uses).label('total_uses')
        ).group_by(Command.name).order_by(db.desc('total_uses')).limit(10).all()
        
        daily_checkins = db.session.query(
            db.func.date(CheckIn.date).label('date'),
            db.func.count(CheckIn.id).label('count')
        ).group_by(db.func.date(CheckIn.date)).order_by(db.desc('date')).limit(30).all()
        
        ticket_stats = db.session.query(
            Ticket.status,
            db.func.count(Ticket.id).label('count')
        ).group_by(Ticket.status).all()
        
        analytics_data = {
            'command_usage': [{'name': name, 'uses': uses} for name, uses in command_usage],
            'daily_checkins': [{'date': date.isoformat(), 'count': count} for date, count in daily_checkins],
            'ticket_stats': [{'status': status, 'count': count} for status, count in ticket_stats]
        }
        
        return render_template('analytics.html', analytics=analytics_data)
    
    @app.route('/api/guild-config/<guild_id>', methods=['GET', 'PUT'])
    @login_required
    def api_guild_config(guild_id):
        """Guild configuration API"""
        guild_config = GuildConfig.query.filter_by(guild_id=guild_id).first()
        
        if request.method == 'GET':
            if not guild_config:
                return jsonify({'error': 'Guild not found', 'success': False}), 404
            
            return jsonify({
                'guild_id': guild_config.guild_id,
                'guild_name': guild_config.guild_name,
                'prefix': guild_config.prefix,
                'currency_name': guild_config.currency_name,
                'currency_symbol': guild_config.currency_symbol,
                'daily_reward': guild_config.daily_reward,
                'auto_mod_enabled': guild_config.auto_mod_enabled,
                'economy_enabled': guild_config.economy_enabled,
                'tickets_enabled': guild_config.tickets_enabled
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if not guild_config:
                guild_config = GuildConfig(guild_id=guild_id)
                db.session.add(guild_config)
            
            # Update configuration
            for key, value in data.items():
                if hasattr(guild_config, key):
                    setattr(guild_config, key, value)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Guild configuration updated with Victorian precision! ⚙️',
                'success': True
            })
    
    # WebSocket route for real-time updates
    @app.route('/api/ws')
    def websocket():
        """WebSocket endpoint for real-time updates"""
        # This would be implemented with flask-socketio in a real application
        return jsonify({'message': 'WebSocket endpoint - implement with flask-socketio'})
