from typing import Union
from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from _bot import bot
from utils.multiuser_db import UsersDB
from .start import start


def register(d: Union[Message, CallbackQuery]):
    """Handle pendaftaran pengguna baru."""
    user_id = d.from_user.id
    
    # Cek apakah pengguna sudah terdaftar
    user = UsersDB().get_by_id(user_id)
    
    if user:
        msg = bot.send_message(
            text=f'✅ Anda sudah terdaftar di sistem.\nSaldo Anda: Rp {user["balance"]:,.0f}',
            chat_id=user_id
        )
        start(msg)
        return
    
    # Proses pendaftaran
    username = d.from_user.username or ""
    first_name = d.from_user.first_name or "Pengguna"
    
    try:
        UsersDB().register(user_id, username, first_name)
        
        msg = bot.send_message(
            text=f'✅ Pendaftaran berhasil!\n\nSelamat datang {first_name}!\n\nSaldo awal Anda: Rp 0',
            chat_id=user_id
        )
        
        # Setelah berhasil mendaftar, arahkan ke menu utama
        start(msg)
        
    except Exception as e:
        bot.send_message(
            text=f'❌ Gagal mendaftar: {str(e)}',
            chat_id=user_id
        )


def check_auth(user_id: int):
    """Cek apakah pengguna sudah terdaftar."""
    user = UsersDB().get_by_id(user_id)
    return user is not None


def is_admin(user_id: int):
    """Cek apakah pengguna adalah admin."""
    user = UsersDB().get_by_id(user_id)
    return user and user.get('is_admin', False)


def update_last_login(user_id: int):
    """Update login terakhir pengguna."""
    try:
        UsersDB().update_last_login(user_id)
    except Exception:
        # Abaikan kesalahan
        pass


def login(d: Message):
    """
    Handle login pengguna.
    Login berdasarkan Telegram ID, jadi tidak memerlukan password.
    Function ini hanya akan mengupdate last_login timestamp.
    """
    user_id = d.from_user.id
    
    # Cek apakah pengguna sudah terdaftar
    user = UsersDB().get_by_id(user_id)
    
    if not user:
        bot.send_message(
            text='❌ Anda belum terdaftar. Silakan lakukan pendaftaran terlebih dahulu.',
            chat_id=user_id
        )
        register(d)
        return
    
    # Update last login
    update_last_login(user_id)
    
    # Arahkan ke menu utama
    start(d)
