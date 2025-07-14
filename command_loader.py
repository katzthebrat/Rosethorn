"""
Command loader utility for the Rosethorn Discord bot.
Handles dynamic loading and management of commands from the commands directory.
"""
import os
import importlib
import inspect
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CommandLoader:
    """Handles dynamic loading of commands from the commands directory."""
    
    def __init__(self, bot, commands_dir: str = "commands"):
        """Initialize the command loader."""
        self.bot = bot
        self.commands_dir = commands_dir
        self.loaded_commands: Dict[str, Any] = {}
    
    def discover_commands(self) -> List[str]:
        """Discover all command files in the commands directory."""
        if not os.path.exists(self.commands_dir):
            logger.warning(f"Commands directory '{self.commands_dir}' not found")
            return []
        
        command_files = []
        
        for file in os.listdir(self.commands_dir):
            if file.endswith('.py') and not file.startswith('__'):
                # Remove .py extension to get module name
                module_name = file[:-3]
                command_files.append(module_name)
        
        logger.info(f"Discovered {len(command_files)} command files: {command_files}")
        return command_files
    
    def load_command(self, command_name: str) -> bool:
        """Load a single command by name."""
        try:
            # Import the command module
            module_path = f"{self.commands_dir}.{command_name}"
            
            # Handle reloading if already loaded
            if module_path in self.loaded_commands:
                importlib.reload(self.loaded_commands[module_path])
            
            module = importlib.import_module(module_path)
            
            # Look for setup function
            if hasattr(module, 'setup'):
                setup_func = getattr(module, 'setup')
                
                # Call setup function with bot instance
                command_instance = setup_func(self.bot)
                
                # Store the loaded command
                self.loaded_commands[command_name] = {
                    'module': module,
                    'instance': command_instance
                }
                
                logger.info(f"Successfully loaded command: {command_name}")
                return True
            else:
                logger.error(f"Command {command_name} missing setup() function")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load command {command_name}: {e}")
            return False
    
    def load_all_commands(self) -> int:
        """Load all discovered commands."""
        command_files = self.discover_commands()
        loaded_count = 0
        
        for command_name in command_files:
            if self.load_command(command_name):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count}/{len(command_files)} commands successfully")
        return loaded_count
    
    def reload_command(self, command_name: str) -> bool:
        """Reload a specific command."""
        logger.info(f"Reloading command: {command_name}")
        return self.load_command(command_name)
    
    def reload_all_commands(self) -> int:
        """Reload all commands."""
        logger.info("Reloading all commands...")
        
        # Clear existing commands from bot
        self.bot.clear()
        self.loaded_commands.clear()
        
        # Reload all commands
        return self.load_all_commands()
    
    def get_loaded_commands(self) -> List[str]:
        """Get list of currently loaded command names."""
        return list(self.loaded_commands.keys())
    
    def unload_command(self, command_name: str) -> bool:
        """Unload a specific command."""
        if command_name in self.loaded_commands:
            # Remove from bot
            command = self.bot.get_command(command_name)
            if command:
                self.bot.remove_command(command_name)
            
            # Remove from our tracking
            del self.loaded_commands[command_name]
            
            logger.info(f"Unloaded command: {command_name}")
            return True
        else:
            logger.warning(f"Command {command_name} not found in loaded commands")
            return False