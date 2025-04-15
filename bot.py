import json
import logging
import traceback
from os import environ
from typing import Union
import urllib.parse as urlparse
from urllib.parse import parse_qs

import telebot
from telebot.types import CallbackQuery, Message

from _bot import bot
# noinspection PyUnresolvedReferences
from modules import *
from modules.register import check_auth, is_admin

bot_admins = json.loads(environ.get('bot_admins'))
multi_user_mode = environ.get('multi_user', 'False').lower() == 'true'

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

# Perintah untuk semua pengguna (termasuk yang belum terdaftar)
public_commands = {
    '/start': 'start',
    '/register': 'register',
    '/login': 'login',
    '/help': 'start',
}

# Perintah untuk pengguna yang sudah terdaftar
user_commands = {
    '/wallet': 'wallet',
    '/topup': 'wallet',
    '/auto_order': 'auto_order',
    '/order': 'auto_order',
}

# Perintah khusus untuk admin
admin_commands = {
    '/add_do': 'add_account',
    '/sett_do': 'manage_accounts',
    '/bath_do': 'batch_test_accounts',
    '/add_vps': 'create_droplet',
    '/sett_vps': 'manage_droplets',
}


@bot.message_handler(content_types=['text'])
def text_handler(m: Message):
    try:
        logger.info(m)
        
        # Perintah untuk semua pengguna
        if m.text in public_commands.keys():
            globals()[public_commands[m.text]](m)
            return
        
        # Mode multi-user diaktifkan
        if multi_user_mode:
            # Perintah untuk pengguna yang sudah terdaftar
            if m.text in user_commands.keys():
                if check_auth(m.from_user.id):
                    globals()[user_commands[m.text]](m)
                else:
                    bot.send_message(
                        text='🚫 Anda belum terdaftar. Gunakan /register untuk mendaftar terlebih dahulu.',
                        chat_id=m.from_user.id
                    )
                return
            
            # Perintah untuk admin
            if m.text in admin_commands.keys():
                if is_admin(m.from_user.id) or m.from_user.id in bot_admins:
                    globals()[admin_commands[m.text]](m)
                else:
                    bot.send_message(
                        text='🚫 Anda tidak memiliki izin untuk menggunakan perintah ini.',
                        chat_id=m.from_user.id
                    )
                return
        
        # Mode single-user (hanya admin)
        else:
            # Gabungkan semua perintah
            all_commands = {**public_commands, **user_commands, **admin_commands}
            
            if m.from_user.id not in bot_admins:
                bot.send_message(
                    text='🚫 Anda tidak memiliki izin untuk menggunakan bot ini.',
                    chat_id=m.from_user.id
                )
                return
            
            if m.text in all_commands.keys():
                globals()[all_commands[m.text]](m)

    except Exception as e:
        traceback.print_exc()
        handle_exception(m, e)


@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call: CallbackQuery):
    try:
        logger.info(call)
        
        callback_data = urlparse.urlparse(call.data)
        func_name = callback_data.path
        data = parse_qs(callback_data.query)
        
        # Callbacks umum yang dapat diakses semua pengguna
        public_callbacks = ['start', 'register', 'login']
        
        # Cek apakah mode multi-user diaktifkan
        if multi_user_mode:
            # Callbacks untuk user terdaftar
            user_callbacks = ['wallet', 'auto_order']
            
            # Callbacks untuk admin
            admin_callbacks = [
                'add_account', 'manage_accounts', 'batch_test_accounts',
                'account_detail', 'delete_account', 'batch_test_delete_accounts',
                'create_droplet', 'manage_droplets', 'list_droplets',
                'droplet_detail', 'droplet_actions'
            ]
            
            # Pengecekan akses
            if func_name in public_callbacks:
                # Semua pengguna bisa mengakses
                pass
            elif func_name in user_callbacks:
                # Hanya user terdaftar
                if not check_auth(call.from_user.id):
                    bot.answer_callback_query(
                        callback_query_id=call.id,
                        text='Anda belum terdaftar. Silakan register terlebih dahulu.',
                        show_alert=True
                    )
                    return
            elif func_name in admin_callbacks:
                # Hanya admin
                if not (is_admin(call.from_user.id) or call.from_user.id in bot_admins):
                    bot.answer_callback_query(
                        callback_query_id=call.id,
                        text='Anda tidak memiliki izin untuk mengakses fitur ini.',
                        show_alert=True
                    )
                    return
        else:
            # Mode single-user, hanya admin
            if call.from_user.id not in bot_admins:
                bot.send_message(
                    text='🚫 Anda tidak memiliki izin untuk menggunakan bot ini.',
                    chat_id=call.from_user.id
                )
                return
        
        # Eksekusi fungsi callback
        if func_name in globals():
            args = [call]
            if len(data.keys()) > 0:
                args.append(data)

            globals()[func_name](*args)

    except Exception as e:
        traceback.print_exc()
        handle_exception(call, e)


def handle_exception(d: Union[Message, CallbackQuery], e):
    bot.send_message(
        text=f'❌ Terjadi kesalahan\n'
             f'<code>{e}</code>',
        chat_id=d.from_user.id,
        parse_mode='HTML'
    )
