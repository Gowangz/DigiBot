from typing import Union

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import json
from os import environ

from _bot import bot
from utils.multiuser_db import UsersDB, TransactionsDB
from modules.register import is_admin

bot_admins = json.loads(environ.get('bot_admins'))


def manage_users(d: Union[Message, CallbackQuery], data: dict = None):
    """Mengelola pengguna (hanya admin)."""
    user_id = d.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(user_id) or user_id in bot_admins):
        bot.send_message(
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            chat_id=user_id
        )
        return
    
    users = UsersDB().get_all_users()
    
    # Siapkan pesan
    msg = '<b>👥 Kelola Pengguna</b>\n\n' \
          f'Total Pengguna: {len(users)}\n\n'
    
    # Siapkan markup
    markup = InlineKeyboardMarkup()
    
    # Tampilkan pengguna terbaru (10 teratas)
    recent_users = sorted(users, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    
    for user in recent_users:
        user_id = user.get('user_id')
        username = user.get('username', '')
        first_name = user.get('first_name', 'Pengguna')
        is_admin_flag = '👑 ' if user.get('is_admin', False) else ''
        
        display_name = first_name
        if username:
            display_name += f' (@{username})'
        
        markup.add(
            InlineKeyboardButton(
                text=f'{is_admin_flag}{display_name}',
                callback_data=f'user_detail?user_id={user_id}'
            )
        )
    
    # Tambahkan tombol pencarian dan kembali
    markup.row(
        InlineKeyboardButton(
            text='🔍 Cari Pengguna',
            callback_data='search_user'
        )
    )
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali ke Menu',
            callback_data='start'
        )
    )
    
    # Kirim pesan
    if isinstance(d, Message):
        bot.send_message(
            text=msg,
            chat_id=d.from_user.id,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:  # CallbackQuery
        bot.edit_message_text(
            text=msg,
            chat_id=d.from_user.id,
            message_id=d.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )


def user_detail(call: CallbackQuery, data: dict):
    """Menampilkan detail pengguna."""
    admin_id = call.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            show_alert=True
        )
        return
    
    user_id = int(data.get('user_id', [0])[0])
    user = UsersDB().get_by_id(user_id)
    
    if not user:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Pengguna tidak ditemukan',
            show_alert=True
        )
        return
    
    # Siapkan informasi pengguna
    username = user.get('username', '')
    first_name = user.get('first_name', 'Pengguna')
    balance = user.get('balance', 0)
    is_admin_flag = user.get('is_admin', False)
    created_at = user.get('created_at', '')
    last_login = user.get('last_login', '')
    
    # Ambil transaksi terakhir
    transactions = TransactionsDB().get_by_user(user_id)
    transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_transactions = transactions[:5]
    
    # Siapkan pesan
    msg = f'<b>👤 Detail Pengguna</b>\n\n' \
          f'ID: <code>{user_id}</code>\n' \
          f'Nama: {first_name}\n'
    
    if username:
        msg += f'Username: @{username}\n'
    
    msg += f'Saldo: <b>Rp {balance:,}</b>\n' \
           f'Status Admin: {"✅ Ya" if is_admin_flag else "❌ Tidak"}\n' \
           f'Terdaftar: {created_at}\n' \
           f'Login Terakhir: {last_login}\n\n'
    
    if recent_transactions:
        msg += '<b>Transaksi Terakhir:</b>\n'
        for tx in recent_transactions:
            amount = tx.get('amount', 0)
            tx_type = tx.get('type', '')
            timestamp = tx.get('timestamp', '')
            
            if tx_type == 'topup':
                msg += f'📥 +Rp {amount:,} - {timestamp}\n'
            elif tx_type == 'purchase':
                msg += f'📤 -Rp {abs(amount):,} - {timestamp}\n'
            else:
                msg += f'🔄 Rp {amount:,} - {tx_type} - {timestamp}\n'
    
    # Siapkan markup
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Tombol manajemen
    markup.add(
        InlineKeyboardButton(
            text='💰 Tambah Saldo',
            callback_data=f'add_balance?user_id={user_id}'
        ),
        InlineKeyboardButton(
            text='📝 Edit Saldo',
            callback_data=f'edit_balance?user_id={user_id}'
        )
    )
    
    # Tombol admin
    if is_admin_flag:
        markup.add(
            InlineKeyboardButton(
                text='👑 Hapus Admin',
                callback_data=f'toggle_admin?user_id={user_id}&action=remove'
            )
        )
    else:
        markup.add(
            InlineKeyboardButton(
                text='👑 Jadikan Admin',
                callback_data=f'toggle_admin?user_id={user_id}&action=add'
            )
        )
    
    # Tombol transaksi
    markup.row(
        InlineKeyboardButton(
            text='📊 Semua Transaksi',
            callback_data=f'user_transactions?user_id={user_id}'
        )
    )
    
    # Tombol kembali
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data='manage_users'
        )
    )
    
    # Kirim pesan
    bot.edit_message_text(
        text=msg,
        chat_id=admin_id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )


def add_balance(call: CallbackQuery, data: dict):
    """Menambahkan saldo pengguna."""
    admin_id = call.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            show_alert=True
        )
        return
    
    user_id = int(data.get('user_id', [0])[0])
    user = UsersDB().get_by_id(user_id)
    
    if not user:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Pengguna tidak ditemukan',
            show_alert=True
        )
        return
    
    # Siapkan pesan untuk input jumlah
    first_name = user.get('first_name', 'Pengguna')
    balance = user.get('balance', 0)
    
    msg = f'<b>💰 Tambah Saldo</b>\n\n' \
          f'Pengguna: {first_name}\n' \
          f'Saldo Saat Ini: <b>Rp {balance:,}</b>\n\n' \
          f'Masukkan jumlah saldo yang ingin ditambahkan (dalam Rupiah):\n\n' \
          f'Contoh: 100000 untuk Rp 100.000\n\n' \
          f'/cancel untuk membatalkan'
    
    # Edit pesan
    message = bot.edit_message_text(
        text=msg,
        chat_id=admin_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
    
    # Daftarkan handler untuk langkah berikutnya
    bot.register_next_step_handler(message, process_add_balance, user_id)


def process_add_balance(message: Message, user_id: int):
    """Memproses penambahan saldo."""
    admin_id = message.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.send_message(
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            chat_id=admin_id
        )
        return
    
    if message.text == '/cancel':
        user_detail(message, {'user_id': [str(user_id)]})
        return
    
    try:
        amount = int(message.text.strip())
        
        if amount <= 0:
            raise ValueError("Jumlah harus lebih dari 0")
        
        # Tambahkan saldo
        new_balance = UsersDB().update_balance(user_id, amount)
        
        # Tambahkan transaksi dengan detail admin
        TransactionsDB().add(
            user_id=user_id,
            amount=amount,
            type_='topup',
            details=f"Ditambahkan oleh Admin (ID: {admin_id})"
        )
        
        # Beri tahu admin
        bot.send_message(
            text=f'✅ Saldo berhasil ditambahkan.\n\n'
                 f'Jumlah: <b>+Rp {amount:,}</b>\n'
                 f'Saldo Baru: <b>Rp {new_balance:,}</b>',
            chat_id=admin_id,
            parse_mode='HTML'
        )
        
        # Kembali ke detail pengguna
        user_detail(message, {'user_id': [str(user_id)]})
        
    except ValueError as e:
        bot.send_message(
            text=f'❌ Input tidak valid: {str(e)}',
            chat_id=admin_id
        )
        # Coba lagi
        add_balance(message, {'user_id': [str(user_id)]})


def edit_balance(call: CallbackQuery, data: dict):
    """Mengedit saldo pengguna."""
    admin_id = call.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            show_alert=True
        )
        return
    
    user_id = int(data.get('user_id', [0])[0])
    user = UsersDB().get_by_id(user_id)
    
    if not user:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Pengguna tidak ditemukan',
            show_alert=True
        )
        return
    
    # Siapkan pesan untuk input jumlah
    first_name = user.get('first_name', 'Pengguna')
    balance = user.get('balance', 0)
    
    msg = f'<b>📝 Edit Saldo</b>\n\n' \
          f'Pengguna: {first_name}\n' \
          f'Saldo Saat Ini: <b>Rp {balance:,}</b>\n\n' \
          f'Masukkan jumlah saldo baru (dalam Rupiah):\n\n' \
          f'Contoh: 100000 untuk Rp 100.000\n\n' \
          f'/cancel untuk membatalkan'
    
    # Edit pesan
    message = bot.edit_message_text(
        text=msg,
        chat_id=admin_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
    
    # Daftarkan handler untuk langkah berikutnya
    bot.register_next_step_handler(message, process_edit_balance, user_id, balance)


def process_edit_balance(message: Message, user_id: int, old_balance: int):
    """Memproses pengeditan saldo."""
    admin_id = message.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.send_message(
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            chat_id=admin_id
        )
        return
    
    if message.text == '/cancel':
        user_detail(message, {'user_id': [str(user_id)]})
        return
    
    try:
        new_balance = int(message.text.strip())
        
        if new_balance < 0:
            raise ValueError("Saldo tidak boleh negatif")
        
        # Hitung selisih
        difference = new_balance - old_balance
        
        # Update saldo di database
        UsersDB().users.update({'balance': new_balance}, doc_ids=[user_id])
        
        # Tambahkan transaksi dengan detail perubahan
        transaction_type = 'topup' if difference > 0 else 'withdraw'
        TransactionsDB().add(
            user_id=user_id,
            amount=difference,
            type_=transaction_type,
            details=f"Diedit oleh Admin (ID: {admin_id})"
        )
        
        # Beri tahu admin
        bot.send_message(
            text=f'✅ Saldo berhasil diubah.\n\n'
                 f'Saldo Lama: <b>Rp {old_balance:,}</b>\n'
                 f'Saldo Baru: <b>Rp {new_balance:,}</b>\n'
                 f'Perubahan: <b>{"+Rp " if difference >= 0 else "-Rp "}{abs(difference):,}</b>',
            chat_id=admin_id,
            parse_mode='HTML'
        )
        
        # Kembali ke detail pengguna
        user_detail(message, {'user_id': [str(user_id)]})
        
    except ValueError as e:
        bot.send_message(
            text=f'❌ Input tidak valid: {str(e)}',
            chat_id=admin_id
        )
        # Coba lagi
        edit_balance(message, {'user_id': [str(user_id)]})


def toggle_admin(call: CallbackQuery, data: dict):
    """Mengaktifkan/menonaktifkan status admin pengguna."""
    admin_id = call.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            show_alert=True
        )
        return
    
    user_id = int(data.get('user_id', [0])[0])
    action = data.get('action', [''])[0]
    
    user = UsersDB().get_by_id(user_id)
    if not user:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Pengguna tidak ditemukan',
            show_alert=True
        )
        return
    
    # Update status admin
    try:
        is_admin_flag = action == 'add'
        UsersDB().users.update({'is_admin': is_admin_flag}, doc_ids=[user_id])
        
        # Beri tahu tentang perubahan
        status_text = 'menjadi Admin' if is_admin_flag else 'dihapus dari Admin'
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'✅ Status pengguna berhasil diubah {status_text}',
            show_alert=True
        )
        
        # Kembali ke detail pengguna
        user_detail(call, {'user_id': [str(user_id)]})
        
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'❌ Gagal mengubah status admin: {str(e)}',
            show_alert=True
        )


def user_transactions(call: CallbackQuery, data: dict):
    """Menampilkan transaksi pengguna."""
    admin_id = call.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(admin_id) or admin_id in bot_admins):
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
            show_alert=True
        )
        return
    
    user_id = int(data.get('user_id', [0])[0])
    user = UsersDB().get_by_id(user_id)
    
    if not user:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Pengguna tidak ditemukan',
            show_alert=True
        )
        return
    
    # Ambil transaksi
    transactions = TransactionsDB().get_by_user(user_id)
    transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Siapkan pesan
    first_name = user.get('first_name', 'Pengguna')
    username = user.get('username', '')
    display_name = first_name
    if username:
        display_name += f' (@{username})'
    
    msg = f'<b>📊 Transaksi {display_name}</b>\n\n'
    
    if not transactions:
        msg += 'Belum ada transaksi.'
    else:
        for tx in transactions:
            amount = tx.get('amount', 0)
            tx_type = tx.get('type', '')
            timestamp = tx.get('timestamp', '')
            details = tx.get('details', '')
            reference_id = tx.get('reference_id', '')
            
            # Format transaksi
            if tx_type == 'topup':
                msg += f'📥 <b>+Rp {amount:,}</b> - {timestamp}'
            elif tx_type == 'purchase':
                msg += f'📤 <b>-Rp {abs(amount):,}</b> - {timestamp}'
            else:
                msg += f'🔄 <b>Rp {amount:,}</b> - {tx_type} - {timestamp}'
            
            if details:
                msg += f' - {details}'
            
            if reference_id:
                msg += f' (Ref: {reference_id})'
            
            msg += '\n'
    
    # Siapkan markup
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data=f'user_detail?user_id={user_id}'
        )
    )
    
    # Kirim pesan
    bot.edit_message_text(
        text=msg,
        chat_id=admin_id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )


def view_transactions(d: Union[Message, CallbackQuery], data: dict = None):
    """Menampilkan semua transaksi (untuk admin)."""
    user_id = d.from_user.id
    
    # Periksa apakah pengguna adalah admin
    if not (is_admin(user_id) or user_id in bot_admins):
        if isinstance(d, Message):
            bot.send_message(
                text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
                chat_id=user_id
            )
        else:
            bot.answer_callback_query(
                callback_query_id=d.id,
                text='🚫 Anda tidak memiliki izin untuk mengakses fitur ini.',
                show_alert=True
            )
        return
    
    # Ambil parameter filter jika ada
    data = data or {}
    tx_type = data.get('type', ['all'])[0]
    page = int(data.get('page', ['1'])[0])
    per_page = 10
    
    # Ambil semua transaksi dari database
    transactions = []
    
    # Simulasi untuk mendapatkan semua transaksi dari semua pengguna
    db = TransactionsDB()
    transaction_table = db.transactions.all()
    
    # Filter berdasarkan tipe jika diperlukan
    if tx_type != 'all':
        transaction_table = [tx for tx in transaction_table if tx.get('type') == tx_type]
    
    # Urutkan berdasarkan waktu (terbaru dulu)
    transaction_table.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Paginasi
    total_pages = (len(transaction_table) + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Ambil transaksi untuk halaman saat ini
    current_page_transactions = transaction_table[start_idx:end_idx]
    
    # Siapkan pesan
    msg = f'<b>📊 Daftar Transaksi</b>\n\n'
    
    if not current_page_transactions:
        msg += 'Belum ada transaksi.'
    else:
        # Ambil informasi pengguna
        user_cache = {}
        
        for tx in current_page_transactions:
            tx_user_id = tx.get('user_id')
            amount = tx.get('amount', 0)
            tx_type = tx.get('type', '')
            timestamp = tx.get('timestamp', '')
            details = tx.get('details', '')
            
            # Dapatkan info pengguna (dengan cache)
            if tx_user_id not in user_cache:
                user = UsersDB().get_by_id(tx_user_id)
                if user:
                    first_name = user.get('first_name', 'Pengguna')
                    username = user.get('username', '')
                    display_name = first_name
                    if username:
                        display_name += f' (@{username})'
                    user_cache[tx_user_id] = display_name
                else:
                    user_cache[tx_user_id] = f'User {tx_user_id}'
            
            user_display = user_cache[tx_user_id]
            
            # Format transaksi
            if tx_type == 'topup':
                msg += f'📥 <b>+Rp {amount:,}</b> - {user_display} - {timestamp}'
            elif tx_type == 'purchase':
                msg += f'📤 <b>-Rp {abs(amount):,}</b> - {user_display} - {timestamp}'
            else:
                msg += f'🔄 <b>Rp {amount:,}</b> - {tx_type} - {user_display} - {timestamp}'
            
            if details:
                msg += f' - {details}'
            
            msg += '\n'
        
        # Tambahkan info paginasi
        msg += f'\nHalaman {page} dari {total_pages}'
    
    # Siapkan markup untuk filter dan navigasi
    markup = InlineKeyboardMarkup(row_width=3)
    
    # Tombol filter
    filter_buttons = [
        InlineKeyboardButton(
            text=f'{"✅" if tx_type == "all" else ""} Semua',
            callback_data='view_transactions?type=all&page=1'
        ),
        InlineKeyboardButton(
            text=f'{"✅" if tx_type == "topup" else ""} Top Up',
            callback_data='view_transactions?type=topup&page=1'
        ),
        InlineKeyboardButton(
            text=f'{"✅" if tx_type == "purchase" else ""} Pembelian',
            callback_data='view_transactions?type=purchase&page=1'
        )
    ]
    markup.add(*filter_buttons)
    
    # Tombol navigasi halaman
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text='⬅️ Sebelumnya',
                callback_data=f'view_transactions?type={tx_type}&page={page-1}'
            )
        )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text='Selanjutnya ➡️',
                callback_data=f'view_transactions?type={tx_type}&page={page+1}'
            )
        )
    
    markup.row(*nav_buttons)
    
    # Tombol kembali
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali ke Menu',
            callback_data='start'
        )
    )
    
    # Kirim pesan
    if isinstance(d, Message):
        bot.send_message(
            text=msg,
            chat_id=user_id,
            parse_mode='HTML',
            reply_markup=markup
        )
    else:  # CallbackQuery
        bot.edit_message_text(
            text=msg,
            chat_id=user_id,
            message_id=d.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
