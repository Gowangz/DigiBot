import os
import sys
import json
import logging
import signal
from typing import NoReturn
from tinydb import TinyDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger('main')

def load_config() -> None:
    """Load and validate configuration."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required bot configuration
        bot_config = config.get('BOT', {})
        required_fields = ['NAME', 'TOKEN', 'ADMINS']
        missing_fields = [field for field in required_fields if field not in bot_config]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
        
        # Set environment variables
        os.environ['BOT_NAME'] = bot_config['NAME']
        os.environ['BOT_TOKEN'] = bot_config['TOKEN']
        os.environ['BOT_ADMINS'] = json.dumps(bot_config['ADMINS'])
        os.environ['MULTI_USER'] = str(bot_config.get('MULTI_USER', True))
        
        # Payment gateway configuration
        payment_config = bot_config.get('PAYMENT_CONFIG', {})
        required_payment_fields = ['MERCHANT_ID', 'API_KEY', 'DATA_QRIS', 'CALLBACK_URL']
        missing_payment_fields = [field for field in required_payment_fields if not payment_config.get(field)]
        
        if missing_payment_fields:
            logger.warning(f"Missing payment configuration fields: {', '.join(missing_payment_fields)}")
        
        os.environ['PAYMENT_MERCHANT_ID'] = payment_config.get('MERCHANT_ID', '')
        os.environ['PAYMENT_API_KEY'] = payment_config.get('API_KEY', '')
        os.environ['PAYMENT_DATA_QRIS'] = payment_config.get('DATA_QRIS', '')
        os.environ['PAYMENT_CALLBACK_URL'] = payment_config.get('CALLBACK_URL', '')
        os.environ['PAYMENT_CHECK_INTERVAL'] = str(payment_config.get('CHECK_INTERVAL', 5))
        os.environ['PAYMENT_EXPIRE_TIME'] = str(payment_config.get('EXPIRE_TIME', 30))
        
        logger.info("Configuration loaded successfully")
        
    except FileNotFoundError:
        logger.error("config.json not found")
        raise
    except json.JSONDecodeError:
        logger.error("Invalid JSON in config.json")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def setup_database() -> None:
    """Initialize and verify database structure."""
    try:
        # Ensure database directory exists
        db_dir = 'data'
        os.makedirs(db_dir, exist_ok=True)
        
        # Initialize databases
        databases = {
            'users.json': ['users'],
            'transactions.json': ['transactions'],
            'accounts.json': ['accounts'],
            'droplets.json': ['user_droplets']
        }
        
        for db_file, tables in databases.items():
            db_path = os.path.join(db_dir, db_file)
            db = TinyDB(db_path)
            
            # Initialize required tables
            for table in tables:
                if table not in db.tables():
                    db.table(table)
                    logger.info(f"Created table '{table}' in {db_file}")
            
            db.close()
            
        logger.info("Database setup completed")
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise

def signal_handler(signum: int, frame) -> NoReturn:
    """Handle termination signals gracefully."""
    logger.info(f"Received signal {signum}")
    logger.info("Shutting down bot...")
    sys.exit(0)

def start_bot() -> None:
    """Initialize and start the bot."""
    try:
        from bot import bot
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting bot...")
        bot.polling(none_stop=True, interval=1, timeout=60)
        
    except Exception as e:
        logger.error(f"Bot startup failed: {str(e)}")
        raise

def main() -> None:
    """Main entry point with initialization sequence."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        load_config()
        
        # Setup database
        logger.info("Setting up database...")
        setup_database()
        
        # Start bot
        logger.info("Initializing bot...")
        start_bot()
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
