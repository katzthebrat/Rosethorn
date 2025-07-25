import os
import asyncio
import threading
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.serving import make_server
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "rosethorn_gothic_secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///rosethorn.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access the Victorian Gothic Dashboard'
    login_manager.login_message_category = 'gothic-warning'
    
    # Import models to ensure they're registered
    with app.app_context():
        import models
        db.create_all()
        logger.info("🌹 Database tables created successfully")
    
    # Register blueprints
    from dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    return app

def run_bot():
    """Run the Discord bot in a separate thread."""
    try:
        from bot import run_discord_bot
        asyncio.run(run_discord_bot())
    except Exception as e:
        logger.error(f"🥀 Discord bot error: {e}")

def run_flask_app():
    """Run the Flask web application."""
    app = create_app()
    
    # Start Discord bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("🌹 Discord bot started in background thread")
    
    # Run Flask app
    logger.info("🌹 Starting Victorian Gothic Dashboard on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == "__main__":
    run_flask_app()
