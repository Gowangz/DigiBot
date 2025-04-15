from typing import Union
import json
from os import environ

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from _bot import bot
from utils.multiuser_db import UsersDB
from modules.auth import check_auth, is_admin

def register(d: Union[Message, CallbackQuery]):
    """Handle pendaftaran pengguna baru."""
    user_id = d.from_user.id
    
    # Cek apakah sudah terdaftar
    if check_auth(user_id):
        t = '❌ Anda sudah terdaftar.\n\n' \
            'Gunakan /start untuk membuka menu utama.'
        
        if isinstance(d, Message):
            bot.send_message(
                text=t,
                chat_id=user_id
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Anda sudah terdaftar',
                show_alert=True
            )
            bot.edit_message_text(
                text=t,
                chat_id=user_id,
                message_id=d.message.message_id
            )
        return
    
    # Proses pendaftaran
    try:
        UsersDB().register(
            user_id=user_id,
            username=d.from_user.username or '',
            first_name=d.from_user.first_name
        )
        
        t = '✅ Pendaftaran berhasil!\n\n' \
            'Gunakan /start untuk membuka menu utama.'
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='🏠 Menu Utama',
                callback_data='start'
            )
        )
        
        if isinstance(d, Message):
            bot.send_message(
                text=t,
                chat_id=user_id,
                reply_markup=markup
            )
        else:  # CallbackQuery
            bot.edit_message_text(
                text=t,
                chat_id=user_id,
                message_id=d.message.message_id,
                reply_markup=markup
            )
        
    except Exception as e:
        t = f'❌ Pendaftaran gagal: {str(e)}'
        
        if isinstance(d, Message):
            bot.send_message(
                text=t,
                chat_id=user_id
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Pendaftaran gagal',
                show_alert=True
            )
            bot.edit_message_text(
                text=t,
                chat_id=user_id,
                message_id=d.message.message_id
            )
