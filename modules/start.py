import json
import os
from typing import Union

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from _bot import bot
from modules.auth import check_auth, is_admin

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    BOT_CONFIG = config.get('BOT', {})
    bot_name = BOT_CONFIG.get('NAME', 'Asisten DigitalOcean')
    bot_admins = [int(admin_id) for admin_id in BOT_CONFIG.get('ADMINS', [])]
    multi_user_mode = BOT_CONFIG.get('MULTI_USER', True)
except Exception as e:
    # Fallback to environment variables if config file fails
    bot_name = os.environ.get('BOT_NAME', 'Asisten DigitalOcean')
    bot_admins = [int(id) for id in json.loads(os.environ.get('BOT_ADMINS', '[]'))]
    multi_user_mode = os.environ.get('MULTI_USER', 'True').lower() == 'true'


def start(d: Union[Message, CallbackQuery]):
    """
    Fungsi start menampilkan menu utama berdasarkan tingkat akses pengguna.
    """
    user_id = d.from_user.id
    
    try:
        # Cek apakah multi_user_mode diaktifkan
        if multi_user_mode:
            # Cek status pengguna
            if check_auth(user_id):
                # Pengguna terdaftar
                if is_admin(user_id) or user_id in bot_admins:
                    # Admin
                    show_admin_menu(d)
                else:
                    # Pengguna reguler
                    show_user_menu(d)
            else:
                # Pengguna belum terdaftar
                show_register_menu(d)
        else:
            # Mode single-user (hanya admin)
            if user_id in bot_admins:
                show_admin_menu(d)
            else:
                bot.send_message(
                    chat_id=user_id,
                    text='🚫 Maaf, bot ini hanya dapat digunakan oleh admin.',
                    parse_mode='HTML'
                )
    except Exception as e:
        error_msg = f'❌ Terjadi kesalahan saat memuat menu: {str(e)}'
        if isinstance(d, Message):
            bot.send_message(
                chat_id=user_id,
                text=error_msg,
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Terjadi kesalahan',
                show_alert=True
            )


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
    
    try:
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
    except Exception as e:
        error_msg = f'❌ Terjadi kesalahan: {str(e)}'
        if isinstance(d, Message):
            bot.send_message(
                chat_id=d.from_user.id,
                text=error_msg,
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Terjadi kesalahan',
                show_alert=True
            )


def show_user_menu(d: Union[Message, CallbackQuery]):
    """Tampilkan menu untuk pengguna yang sudah terdaftar."""
    try:
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
    except Exception as e:
        error_msg = f'❌ Terjadi kesalahan: {str(e)}'
        if isinstance(d, Message):
            bot.send_message(
                chat_id=d.from_user.id,
                text=error_msg,
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Terjadi kesalahan',
                show_alert=True
            )


def show_admin_menu(d: Union[Message, CallbackQuery]):
    """Tampilkan menu untuk admin."""
    try:
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
        markup.add(
            InlineKeyboardButton(
                text='💰 Edit Harga VPS',
                callback_data='admin_tools?nf=show'
            )
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
    except Exception as e:
        error_msg = f'❌ Terjadi kesalahan: {str(e)}'
        if isinstance(d, Message):
            bot.send_message(
                chat_id=d.from_user.id,
                text=error_msg,
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='Terjadi kesalahan',
                show_alert=True
            )
