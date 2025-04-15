import os
import json
import logging
from typing import Optional

import telebot
from telebot.handler_backends import State, StatesGroup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger('bot')

class BotConfig:
    """Bot configuration handler"""
    def __init__(self):
        self.token: Optional[str] = None
        self.name: Optional[str] = None
        self.admins: list = []
        self.multi_user: bool = True
        self.payment_config: dict = {}
        
        self.load_config()
        
    def load_config(self):
        """Load configuration from config file or environment variables"""
        try:
            # Try loading from config file first
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            bot_config = config.get('BOT', {})
            self.token = bot_config.get('TOKEN')
            self.name = bot_config.get('NAME', 'Asisten DigitalOcean')
            # Convert admin IDs to integers
            self.admins = []
            for admin_id in bot_config.get('ADMINS', []):
                try:
                    self.admins.append(int(admin_id))
                    logger.info(f"Added admin ID: {admin_id}")
                except (ValueError, TypeError):
                    logger.error(f"Invalid admin ID: {admin_id}")
            self.multi_user = bot_config.get('MULTI_USER', True)
            self.payment_config = bot_config.get('PAYMENT_CONFIG', {})
            
            logger.info("Configuration loaded from config.json")
            logger.info(f"Admin IDs: {self.admins}")
            
        except Exception as e:
            logger.warning(f"Failed to load config.json: {str(e)}")
            logger.info("Falling back to environment variables")
            
            # Fallback to environment variables
            self.token = os.environ.get('BOT_TOKEN')
            self.name = os.environ.get('BOT_NAME', 'Asisten DigitalOcean')
            self.admins = [int(id) for id in json.loads(os.environ.get('BOT_ADMINS', '[]'))]
            self.multi_user = os.environ.get('MULTI_USER', 'True').lower() == 'true'
            
            # Load payment config from environment if available
            payment_env_vars = {
                'MERCHANT_ID': os.environ.get('PAYMENT_MERCHANT_ID'),
                'API_KEY': os.environ.get('PAYMENT_API_KEY'),
                'DATA_QRIS': os.environ.get('PAYMENT_DATA_QRIS'),
                'CALLBACK_URL': os.environ.get('PAYMENT_CALLBACK_URL'),
                'CHECK_INTERVAL': int(os.environ.get('PAYMENT_CHECK_INTERVAL', 5)),
                'EXPIRE_TIME': int(os.environ.get('PAYMENT_EXPIRE_TIME', 30))
            }
            self.payment_config = {k: v for k, v in payment_env_vars.items() if v is not None}
        
        # Validate required configuration
        if not self.token:
            raise ValueError("Bot token not found in config.json or environment variables")
        
        if not self.admins:
            logger.warning("No admin users configured")

# States for conversation handling
class BotStates(StatesGroup):
    waiting_for_payment = State()
    waiting_for_confirmation = State()
    waiting_for_droplet_name = State()
    waiting_for_droplet_size = State()
    waiting_for_droplet_region = State()

# Initialize bot configuration
config = BotConfig()

# Initialize bot instance
bot = telebot.TeleBot(
    token=config.token,
    parse_mode='HTML',
    num_threads=4
)

# Configure logger
telebot.logger.setLevel(logging.INFO)

logger.info(f"Bot initialized with name: {config.name}")
logger.info(f"Multi-user mode: {'enabled' if config.multi_user else 'disabled'}")
logger.info(f"Number of admins configured: {len(config.admins)}")
