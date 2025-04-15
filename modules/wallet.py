from typing import Union
import time
import random
import string

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from _bot import bot
from utils.multiuser_db import UsersDB, TransactionsDB
from modules.register import check_auth
from .payment_gateway import initiate_payment, check_payment_status


def wallet(d: Union[Message, CallbackQuery], data: dict = None):
    """Handle menu wallet."""
    data = data or {}
    next_func = data.get('nf', ['show_wallet'])[0]
    
    if not check_auth(d.from_user.id):
        bot.send_message(
            text='❌ Anda belum terdaftar. Silakan lakukan pendaftaran terlebih dahulu.',
            chat_id=d.from_user.id
        )
        from .register import register
        register(d)
        return
    
    if next_func in globals():
        data.pop('nf', None)
        args = [d]
        if len(data.keys()) > 0:
            args.append(data)

        globals()[next_func](*args)


def show_wallet(d: Union[Message, CallbackQuery]):
    """Menampilkan informasi wallet pengguna."""
    user_id = d.from_user.id
    
    try:
        user = UsersDB().get_by_id(user_id)
        if not user:
            raise Exception("Pengguna tidak ditemukan")
        
        balance = user.get('balance', 0)
        
        # Ambil 5 transaksi terakhir
        transactions = TransactionsDB().get_by_user(user_id)
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent_transactions = transactions[:5]
        
        # Buat pesan
        t = f'<b>💰 Wallet</b>\n\n' \
            f'Saldo Anda: <b>Rp {balance:,.0f}</b>\n\n'
        
        if recent_transactions:
            t += '<b>Transaksi Terakhir:</b>\n'
            for tx in recent_transactions:
                amount = tx.get('amount', 0)
                tx_type = tx.get('type', '')
                timestamp = tx.get('timestamp', '')
                
                # Format sesuai jenis transaksi
                if tx_type == 'topup':
                    t += f'📥 <b>+Rp {amount:,.0f}</b> - {timestamp}\n'
                elif tx_type == 'purchase':
                    t += f'📤 <b>-Rp {abs(amount):,.0f}</b> - {timestamp}\n'
                else:
                    t += f'🔄 <b>Rp {amount:,.0f}</b> - {tx_type} - {timestamp}\n'
            
            t += '\n'
        
        # Buat markup
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                text='💵 Top Up',
                callback_data='wallet?nf=topup_options'
            ),
            InlineKeyboardButton(
                text='📋 Histori Lengkap',
                callback_data='wallet?nf=show_history'
            ),
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
                text=t,
                chat_id=user_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            bot.edit_message_text(
                text=t,
                chat_id=user_id,
                message_id=d.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        error_msg = f'❌ Terjadi kesalahan: {str(e)}'
        
        if isinstance(d, Message):
            bot.send_message(
                text=error_msg,
                chat_id=user_id
            )
        else:  # CallbackQuery
            bot.answer_callback_query(
                callback_query_id=d.id,
                text=error_msg,
                show_alert=True
            )


def topup_options(call: CallbackQuery):
    """Menampilkan opsi nominal top up."""
    user_id = call.from_user.id
    
    t = '<b>💵 Top Up Wallet</b>\n\n' \
        'Silakan pilih nominal top up:'
    
    # Opsi nominal top up
    options = [
        ('Rp 50.000', 50000),
        ('Rp 100.000', 100000),
        ('Rp 200.000', 200000),
        ('Rp 500.000', 500000),
        ('Rp 1.000.000', 1000000),
    ]
    
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for label, amount in options:
        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f'wallet?nf=process_topup&amount={amount}'
            )
        )
    
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(
            text='🔢 Nominal Lain',
            callback_data='wallet?nf=custom_topup'
        )
    )
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data='wallet?nf=show_wallet'
        )
    )
    
    bot.edit_message_text(
        text=t,
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='HTML'
    )


def custom_topup(call: CallbackQuery):
    """Menangani top up dengan nominal kustom."""
    user_id = call.from_user.id
    
    t = '<b>💵 Top Up Wallet</b>\n\n' \
        'Silakan masukkan nominal top up (dalam Rupiah, minimal Rp 10.000):\n\n' \
        'Contoh: 75000 untuk Rp 75.000\n\n' \
        '/cancel untuk membatalkan'
    
    msg = bot.edit_message_text(
        text=t,
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
    
    bot.register_next_step_handler(msg, process_custom_topup)


def process_custom_topup(m: Message):
    """Memproses jumlah top up kustom dari input pengguna."""
    user_id = m.from_user.id
    
    if m.text == '/cancel':
        wallet(m, {'nf': ['show_wallet']})
        return
    
    try:
        amount = int(m.text.strip())
        
        if amount < 10000:
            raise ValueError("Minimal top up Rp 10.000")
        
        process_topup(m, {'amount': [str(amount)]})
        
    except ValueError as e:
        bot.send_message(
            text=f'❌ Input tidak valid: {str(e)}',
            chat_id=user_id
        )
        # Kirim kembali menu top up
        wallet(m, {'nf': ['topup_options']})


def process_topup(d: Union[Message, CallbackQuery], data: dict):
    """Memproses top up dengan nominal yang dipilih."""
    user_id = d.from_user.id
    amount = int(data.get('amount', [0])[0])
    
    if amount <= 0:
        # Jika nominal tidak valid
        bot.send_message(
            text='❌ Nominal top up tidak valid.',
            chat_id=user_id
        )
        return wallet(d, {'nf': ['topup_options']})
    
    # Buat referensi ID untuk transaksi
    reference_id = generate_reference_id()
    
    # Inisiasi pembayaran
    payment_url, status = initiate_payment(user_id, amount, reference_id)
    
    if not status:
        # Jika gagal memulai pembayaran
        bot.send_message(
            text='❌ Gagal memulai proses pembayaran. Silakan coba lagi nanti.',
            chat_id=user_id
        )
        return wallet(d, {'nf': ['show_wallet']})
    
    # Kirim instruksi pembayaran
    t = f'<b>💵 Top Up Rp {amount:,.0f}</b>\n\n' \
        f'ID Transaksi: <code>{reference_id}</code>\n\n' \
        f'Status: <b>Menunggu Pembayaran</b>\n\n' \
        f'Silakan lakukan pembayaran melalui link berikut:\n' \
        f'<a href="{payment_url}">Link Pembayaran</a>\n\n' \
        f'Saldo akan otomatis ditambahkan setelah pembayaran selesai.'
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(
            text='🔄 Cek Status',
            callback_data=f'wallet?nf=check_payment&ref={reference_id}'
        )
    )
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali ke Wallet',
            callback_data='wallet?nf=show_wallet'
        )
    )
    
    if isinstance(d, Message):
        bot.send_message(
            text=t,
            chat_id=user_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:  # CallbackQuery
        bot.edit_message_text(
            text=t,
            chat_id=user_id,
            message_id=d.message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )


def check_payment(call: CallbackQuery, data: dict):
    """Memeriksa status pembayaran."""
    user_id = call.from_user.id
    reference_id = data.get('ref', [''])[0]
    
    if not reference_id:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ ID Referensi tidak valid.',
            show_alert=True
        )
        return
    
    # Periksa status pembayaran
    status, amount = check_payment_status(reference_id)
    
    if status == 'completed':
        # Jika pembayaran berhasil, tambahkan saldo
        try:
            new_balance = UsersDB().update_balance(user_id, amount)
            
            t = f'<b>✅ Pembayaran Berhasil!</b>\n\n' \
                f'ID Transaksi: <code>{reference_id}</code>\n' \
                f'Jumlah: <b>Rp {amount:,.0f}</b>\n' \
                f'Saldo Baru: <b>Rp {new_balance:,.0f}</b>\n\n' \
                f'Terima kasih atas top up Anda.'
            
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton(
                    text='⬅️ Kembali ke Wallet',
                    callback_data='wallet?nf=show_wallet'
                )
            )
            
            bot.edit_message_text(
                text=t,
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            bot.answer_callback_query(
                callback_query_id=call.id,
                text=f'❌ Terjadi kesalahan: {str(e)}',
                show_alert=True
            )
    
    elif status == 'pending':
        # Jika masih pending
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='⏳ Pembayaran masih dalam proses. Silakan coba cek kembali beberapa saat lagi.',
            show_alert=True
        )
    
    else:
        # Jika gagal atau status lainnya
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'❌ Status pembayaran: {status}. Silakan hubungi admin jika Anda sudah melakukan pembayaran.',
            show_alert=True
        )


def show_history(call: CallbackQuery):
    """Menampilkan histori transaksi lengkap."""
    user_id = call.from_user.id
    
    try:
        transactions = TransactionsDB().get_by_user(user_id)
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if not transactions:
            t = '<b>📋 Histori Transaksi</b>\n\n' \
                'Belum ada transaksi.'
        else:
            t = '<b>📋 Histori Transaksi</b>\n\n'
            
            for tx in transactions:
                amount = tx.get('amount', 0)
                tx_type = tx.get('type', '')
                timestamp = tx.get('timestamp', '')
                details = tx.get('details', '')
                
                # Format sesuai jenis transaksi
                if tx_type == 'topup':
                    prefix = f'📥 <b>+Rp {amount:,.0f}</b>'
                elif tx_type == 'purchase':
                    prefix = f'📤 <b>-Rp {abs(amount):,.0f}</b>'
                else:
                    prefix = f'🔄 <b>Rp {amount:,.0f}</b>'
                
                t += f'{prefix} - {timestamp}'
                if details:
                    t += f' - {details}'
                t += '\n'
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali ke Wallet',
                callback_data='wallet?nf=show_wallet'
            )
        )
        
        bot.edit_message_text(
            text=t,
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'❌ Terjadi kesalahan: {str(e)}',
            show_alert=True
        )


def generate_reference_id():
    """Menghasilkan ID referensi unik untuk transaksi."""
    timestamp = int(time.time())
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TX-{timestamp}-{random_chars}"
