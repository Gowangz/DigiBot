import logging
import traceback
from typing import Union, Dict, Any
import urllib.parse as urlparse
from urllib.parse import parse_qs

from telebot.types import CallbackQuery, Message

from _bot import bot, config, logger
# noinspection PyUnresolvedReferences
from modules import *
from modules.register import check_auth, is_admin
from modules.admin_tools import edit_vps_price, show_vps_prices, ask_new_price, save_new_price

# Add admin_tools functions to globals
globals().update({
    'admin_tools': edit_vps_price,
    'edit_vps_price': edit_vps_price,
    'show_vps_prices': show_vps_prices,
    'ask_new_price': ask_new_price,
    'save_new_price': save_new_price
})

# Configure command handlers
public_commands: Dict[str, str] = {
    '/start': 'start',
    '/register': 'register',
    '/login': 'login',
    '/help': 'start',
}

user_commands: Dict[str, str] = {
    '/wallet': 'wallet',
    '/topup': 'wallet',
    '/auto_order': 'auto_order',
    '/order': 'auto_order',
}

admin_commands: Dict[str, str] = {
    '/add_do': 'add_account',
    '/sett_do': 'manage_accounts',
    '/bath_do': 'batch_test_accounts',
    '/add_vps': 'create_droplet',
    '/sett_vps': 'manage_droplets',
    '/edit_vps_price': 'edit_vps_price',
}

# Configure callback handlers
public_callbacks: list = ['start', 'register', 'login']

user_callbacks: list = ['wallet', 'auto_order']

admin_callbacks: list = [
    'add_account', 'manage_accounts', 'batch_test_accounts',
    'account_detail', 'delete_account', 'batch_test_delete_accounts',
    'create_droplet', 'manage_droplets', 'list_droplets',
    'droplet_detail', 'droplet_actions', 'admin_tools'
]

def validate_command_handler(handler_name: str) -> bool:
    """Validate that command handler exists and is callable."""
    try:
        handler = globals().get(handler_name)
        return callable(handler)
    except Exception as e:
        logger.error(f"Error validating handler {handler_name}: {str(e)}")
        return False

def execute_command_handler(handler_name: str, *args) -> None:
    """Safely execute command handler with error handling."""
    try:
        handler = globals()[handler_name]
        handler(*args)
    except Exception as e:
        logger.error(f"Error executing handler {handler_name}: {str(e)}")
        raise

@bot.message_handler(content_types=['text'])
def text_handler(m: Message):
    """Handle text messages and commands."""
    try:
        user_id = m.from_user.id
        logger.info(f"Received message from user {user_id}: {m.text}")
        
        # Handle public commands
        if m.text in public_commands:
            handler_name = public_commands[m.text]
            if validate_command_handler(handler_name):
                execute_command_handler(handler_name, m)
            return
        
        # Handle multi-user mode commands
        if config.multi_user:
            # Handle user commands
            if m.text in user_commands:
                if check_auth(user_id):
                    handler_name = user_commands[m.text]
                    if validate_command_handler(handler_name):
                        execute_command_handler(handler_name, m)
                else:
                    bot.send_message(
                        text='🚫 Anda belum terdaftar. Gunakan /register untuk mendaftar terlebih dahulu.',
                        chat_id=user_id
                    )
                return
            
            # Handle admin commands
            if m.text in admin_commands:
                logger.info(f"Checking admin access for user {user_id}")
                logger.info(f"Config admins: {config.admins}")
                logger.info(f"Is database admin: {is_admin(user_id)}")
                logger.info(f"User ID type: {type(user_id)}")
                if is_admin(user_id) or int(user_id) in config.admins:
                    handler_name = admin_commands[m.text]
                    if validate_command_handler(handler_name):
                        execute_command_handler(handler_name, m)
                else:
                    bot.send_message(
                        text='🚫 Anda tidak memiliki izin untuk menggunakan perintah ini.',
                        chat_id=user_id
                    )
                return
        
        # Handle single-user mode (admin only)
        else:
            if int(user_id) not in config.admins:
                bot.send_message(
                    text='🚫 Anda tidak memiliki izin untuk menggunakan bot ini.',
                    chat_id=user_id
                )
                return
            
            # Combine all commands for admin
            all_commands = {**public_commands, **user_commands, **admin_commands}
            if m.text in all_commands:
                handler_name = all_commands[m.text]
                if validate_command_handler(handler_name):
                    execute_command_handler(handler_name, m)

    except Exception as e:
        logger.error(f"Error in text handler: {str(e)}\n{traceback.format_exc()}")
        handle_exception(m, e)

@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call: CallbackQuery):
    """Handle callback queries from inline keyboards."""
    try:
        user_id = call.from_user.id
        logger.info(f"Received callback from user {user_id}: {call.data}")
        
        # Parse callback data
        callback_data = urlparse.urlparse(call.data)
        func_name = callback_data.path
        data = parse_qs(callback_data.query)
        
        # Access control for multi-user mode
        if config.multi_user:
            if func_name in user_callbacks and not check_auth(user_id):
                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Anda belum terdaftar. Silakan register terlebih dahulu.',
                    show_alert=True
                )
                return
                
            if func_name in admin_callbacks:
                logger.info(f"Checking admin access for callback from user {user_id}")
                logger.info(f"Config admins: {config.admins}")
                logger.info(f"Is database admin: {is_admin(user_id)}")
                logger.info(f"User ID type: {type(user_id)}")
                if not (is_admin(user_id) or int(user_id) in config.admins):
                    bot.answer_callback_query(
                        callback_query_id=call.id,
                        text='Anda tidak memiliki izin untuk mengakses fitur ini.',
                        show_alert=True
                    )
                    return
        
        # Access control for single-user mode
        else:
            if int(user_id) not in config.admins:
                bot.answer_callback_query(
                    callback_query_id=call.id,
                    text='Anda tidak memiliki izin untuk menggunakan bot ini.',
                    show_alert=True
                )
                return
        
        # Execute callback handler
        if func_name in globals():
            if validate_command_handler(func_name):
                args = [call]
                if data:
                    args.append(data)
                execute_command_handler(func_name, *args)
        else:
            logger.warning(f"Unknown callback handler: {func_name}")
            bot.answer_callback_query(
                callback_query_id=call.id,
                text='Fitur tidak tersedia',
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Error in callback handler: {str(e)}\n{traceback.format_exc()}")
        handle_exception(call, e)

def handle_exception(d: Union[Message, CallbackQuery], e: Exception):
    """Handle and report exceptions."""
    try:
        error_msg = str(e)
        user_id = d.from_user.id
        
        # Log the error
        logger.error(f"Exception for user {user_id}: {error_msg}\n{traceback.format_exc()}")
        
        # Notify user
        if isinstance(d, CallbackQuery):
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Terjadi kesalahan',
                show_alert=True
            )
        
        bot.send_message(
            text=f'❌ Terjadi kesalahan\n'
                 f'<code>{error_msg}</code>',
            chat_id=user_id,
            parse_mode='HTML'
        )
        
        # Notify admins if critical error
        if isinstance(e, (KeyError, AttributeError, ValueError)):
            for admin_id in config.admins:
                try:
                    bot.send_message(
                        text=f'⚠️ Critical Error Report:\n'
                             f'User: {user_id}\n'
                             f'Error: {error_msg}\n'
                             f'Type: {type(e).__name__}',
                        chat_id=str(admin_id)
                    )
                except:
                    continue
                    
    except Exception as notify_error:
        logger.error(f"Error in exception handler: {str(notify_error)}")

# Initialize bot
logger.info(f"Bot {config.name} started")
logger.info(f"Multi-user mode: {'enabled' if config.multi_user else 'disabled'}")
