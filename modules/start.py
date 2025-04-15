import json
from os import environ
from typing import Union

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from _bot import bot
from modules.register import check_auth, is_admin

bot_name = environ.get('bot_name', 'Asisten DigitalOcean')
multi_user_mode = environ.get('multi_user', 'False').lower() == 'true'


def start(d: Union[Message, CallbackQuery]):
    """
    Fungsi start menampilkan menu utama berdasarkan tingkat akses pengguna.
    """
    user_id = d.from_user.id
    
    # Cek apakah multi_user_mode diaktifkan
    if multi_user_mode:
        # Cek status pengguna
        if check_auth(user_id):
            # Pengguna terdaftar
            if is_admin(user_id) or user_id in json.loads(environ.get('bot_admins')):
                # Admin
                show_admin_menu(d)
            else:
                # Pengguna reguler
                show_user_menu(d)
        else:
            # Pengguna belum terdaftar
            show_register_menu(d)
    else:
        # Mode lama (hanya admin)
        show_admin_menu(d)


def show_register_menu(d: Union[Message, CallbackQuery]):
    """Tampilkan menu untuk pengguna yang belum terdaftar."""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            text='📝 Daftar Akun',
            callback_data='register'
        )
    )
    
    t = f'Selamat Datang di <b>{bot_name}</b> 👋\n\n' \
        'Silakan daftar untuk mulai menggunakan layanan kami.\n\n' \
        'Perintah cepat:\n' \
        '/start - Memulai bot\n' \
        '/register - Daftar akun\n' \
        '/help - Bantuan\n' \
        ' \n' \
        '<b>Dev: @yha_bot</b> 👨‍💻\n' \
        '<b>Support: @fightertunnell</b> 🛡️'
    
    if isinstance(d, Message):
        bot.send_message(
            text=t,
            chat_id=d.from_user.id,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:  # CallbackQuery
        bot.edit_message_text(
            text=t,
            chat_id=d.from_user.id,
            message_id=d.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )


def show_user_menu(d: Union[Message, CallbackQuery]):
    """Tampilkan menu untuk pengguna yang sudah terdaftar."""
    # Ambil data pengguna untuk menampilkan saldo
    from utils.multiuser_db import UsersDB
    user_data = UsersDB().get_by_id(d.from_user.id)
    balance = user_data.get('balance', 0) if user_data else 0
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(
            text='💰 Wallet',
            callback_data='wallet?nf=show_wallet'
        ),
        InlineKeyboardButton(
            text='💵 Top Up',
            callback_data='wallet?nf=topup_options'
        ),
        InlineKeyboardButton(
            text='🚀 Auto Order VPS',
            callback_data='auto_order?nf=select_account'
        ),
        InlineKeyboardButton(
            text='🔍 Lihat VPS Saya',
            callback_data='user_droplets?nf=show_droplets'
        ),
    )
    
    t = f'Selamat Datang di <b>{bot_name}</b> 👋\n\n' \
        f'💰 Saldo Anda: <b>Rp {balance:,}</b>\n\n' \
        'Perintah cepat:\n' \
        '/start - Memulai bot\n' \
        '/wallet - Cek saldo dan top up\n' \
        '/order - Auto order VPS\n' \
        ' \n' \
        '<b>Dev: @yha_bot</b> 👨‍💻\n' \
        '<b>Support: @fightertunnell</b> 🛡️'
    
    if isinstance(d, Message):
        bot.send_message(
            text=t,
            chat_id=d.from_user.id,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:  # CallbackQuery
        bot.edit_message_text(
            text=t,
            chat_id=d.from_user.id,
            message_id=d.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )


def show_admin_menu(d: Union[Message, CallbackQuery]):
    """Tampilkan menu untuk admin."""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Menu Admin untuk DigitalOcean
    markup.add(
        InlineKeyboardButton(
            text='➕ Tambah akun',
            callback_data='add_account'
        ),
        InlineKeyboardButton(
            text='⚙️ Kelola akun',
            callback_data='manage_accounts'
        ),
        InlineKeyboardButton(
            text='💧 Buat droplets',
            callback_data='create_droplet'
        ),
        InlineKeyboardButton(
            text='🛠️ Kelola droplets',
            callback_data='manage_droplets'
        ),
    )
    
    # Jika mode multi-user, tambahkan menu admin
    if multi_user_mode:
        markup.add(
            InlineKeyboardButton(
                text='👥 Kelola Pengguna',
                callback_data='manage_users'
            ),
            InlineKeyboardButton(
                text='💳 Transaksi Pengguna',
                callback_data='view_transactions'
            ),
        )
    
    t = f'Selamat Datang <b>{bot_name}</b> 👋\n\n' \
        'Anda dapat mengelola akun DigitalOcean, membuat instance, dll.\n\n' \
        'Perintah cepat:\n' \
        '/start - Memulai bot\n' \
        '/add_do - Tambah akun\n' \
        '/sett_do - Kelola akun\n' \
        '/bath_do - Uji batch akun\n' \
        '/add_vps - Buat droplets\n' \
        '/sett_vps - Kelola droplets\n'
    
    if multi_user_mode:
        t += '/wallet - Cek saldo dan top up\n' \
             '/order - Auto order VPS\n'
    
    t += ' \n' \
         '<b>Dev: @yha_bot</b> 👨‍💻\n' \
         '<b>Support: @fightertunnell</b> 🛡️'
    
    if isinstance(d, Message):
        bot.send_message(
            text=t,
            chat_id=d.from_user.id,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:  # CallbackQuery
        bot.edit_message_text(
            text=t,
            chat_id=d.from_user.id,
            message_id=d.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
