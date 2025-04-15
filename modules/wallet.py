from typing import Union, Dict, Any
import json
import time
from datetime import datetime
from os import environ

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from _bot import bot
from utils.multiuser_db import UsersDB
from modules.auth import check_auth
from modules.payment_gateway import create_payment, check_payment_status, register_payment_callback

def wallet(d: Union[Message, CallbackQuery], data: dict = None) -> None:
    """Main wallet handler function that routes to appropriate functions."""
    data = data or {}
    next_func = data.get('nf', ['show_wallet'])[0]
    
    if next_func == 'show_wallet':
        show_wallet(d)
    elif next_func == 'show_history':
        show_history(d)
    elif next_func == 'topup':
        handle_topup(d)
    elif next_func == 'topup_options':
        show_topup_options(d)
    elif next_func == 'process_topup':
        amount = int(data.get('amount', [0])[0])
        process_topup(d, amount)

def show_wallet(d: Union[Message, CallbackQuery]) -> None:
    """Show wallet menu and balance."""
    user_id = d.from_user.id
    
    try:
        db = UsersDB()
        balance = db.get_balance(user_id)
        
        t = '<b>💰 Wallet</b>\n\n' \
            f'Saldo: <b>Rp {balance:,.0f}</b>'
            
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='💳 Top Up',
                callback_data='wallet?nf=topup_options'
            ),
            InlineKeyboardButton(
                text='📋 Riwayat',
                callback_data='wallet?nf=show_history'
            )
        )
        
        if isinstance(d, Message):
            bot.send_message(
                chat_id=user_id,
                text=t,
                reply_markup=markup,
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            try:
                bot.edit_message_text(
                    text=t,
                    chat_id=user_id,
                    message_id=d.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            except:
                bot.send_message(
                    chat_id=user_id,
                    text=t,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                
    except Exception as e:
        bot.send_message(
            chat_id=user_id,
            text=f'❌ Terjadi kesalahan: {str(e)}'
        )

def show_history(d: Union[Message, CallbackQuery]):
    """Show transaction history."""
    user_id = d.from_user.id
    
    try:
        db = UsersDB()
        transactions = db.get_transactions(user_id, limit=10)
        
        if not transactions:
            t = '<b>📋 Riwayat Transaksi</b>\n\n' \
                'Belum ada riwayat transaksi.'
        else:
            t = '<b>📋 Riwayat Transaksi</b>\n\n'
            for tx in transactions:
                tx_time = datetime.fromtimestamp(tx.get('timestamp', 0))
                tx_type = tx.get('type', '')
                tx_amount = tx.get('amount', 0)
                tx_status = tx.get('status', '')
                tx_ref = tx.get('ref', '')
                
                t += f'📅 {tx_time.strftime("%d/%m/%Y %H:%M")}\n' \
                     f'💰 {"+" if tx_type == "topup" else "-"}Rp {tx_amount:,.0f}\n' \
                     f'📝 Status: {tx_status}\n' \
                     f'🔗 Ref: {tx_ref}\n' \
                     f'{"─" * 20}\n\n'
        
        markup = InlineKeyboardMarkup()
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
                parse_mode='HTML'
            )
        else:  # CallbackQuery
            try:
                bot.edit_message_text(
                    text=t,
                    chat_id=user_id,
                    message_id=d.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            except:
                bot.send_message(
                    text=t,
                    chat_id=user_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
                
    except Exception as e:
        bot.send_message(
            text=f'❌ Terjadi kesalahan: {str(e)}',
            chat_id=user_id
        )

def show_topup_options(d: Union[Message, CallbackQuery]):
    """Show topup amount options."""
    user_id = d.from_user.id
    
    t = '<b>💳 Top Up Saldo</b>\n\n' \
        'Pilih nominal top up:'
        
    amounts = [10000, 20000, 50000, 100000, 200000, 500000]
    
    markup = InlineKeyboardMarkup()
    for i in range(0, len(amounts), 2):
        row = []
        for amount in amounts[i:i+2]:
            row.append(
                InlineKeyboardButton(
                    text=f'Rp {amount:,.0f}',
                    callback_data=f'wallet?nf=process_topup&amount={amount}'
                )
            )
        markup.row(*row)
    
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data='wallet?nf=show_wallet'
        )
    )
    
    if isinstance(d, Message):
        bot.send_message(
            chat_id=user_id,
            text=t,
            reply_markup=markup,
            parse_mode='HTML'
        )
    else:  # CallbackQuery
        try:
            bot.edit_message_text(
                text=t,
                chat_id=user_id,
                message_id=d.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                chat_id=user_id,
                text=t,
                reply_markup=markup,
                parse_mode='HTML'
            )

def process_topup(d: Union[Message, CallbackQuery], amount: int):
    """Process topup request and generate payment."""
    user_id = d.from_user.id
    
    try:
        # Create payment
        payment_data, error = create_payment(user_id, amount)
        
        if error:
            bot.send_message(
                chat_id=user_id,
                text=f'❌ Gagal membuat pembayaran: {error}'
            )
            return
            
        # Register payment callback
        register_payment_callback(
            payment_data['reference_id'],
            lambda data: handle_payment_success(data, user_id, d.message.message_id if isinstance(d, CallbackQuery) else None)
        )
        
        # Send QR code
        caption = f'<b>💳 Pembayaran QRIS</b>\n\n' \
                  f'Nominal: <b>Rp {payment_data["amount"]:,.0f}</b>\n' \
                  f'Ref ID: <code>{payment_data["reference_id"]}</code>\n\n' \
                  f'⏳ Menunggu pembayaran...\n' \
                  f'Pembayaran akan kadaluarsa dalam {payment_data["expire_time"]} menit.'
                  
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali ke Wallet',
                callback_data='wallet?nf=show_wallet'
            )
        )
        
        bot.send_photo(
            chat_id=user_id,
            photo=payment_data['qr_buffer'],
            caption=caption,
            reply_markup=markup,
            parse_mode='HTML'
        )
        
        if isinstance(d, CallbackQuery):
            try:
                bot.delete_message(
                    chat_id=user_id,
                    message_id=d.message.message_id
                )
            except:
                pass
                
    except Exception as e:
        bot.send_message(
            chat_id=user_id,
            text=f'❌ Terjadi kesalahan: {str(e)}'
        )

def handle_payment_success(payment_data: Dict[str, Any], user_id: int, message_id: int) -> None:
    """Handle successful payment notification."""
    try:
        db = UsersDB()
        
        # Update balance
        new_balance = db.update_balance(user_id, payment_data['amount'])
        
        # Add transaction to history
        transaction = {
            'type': 'topup',
            'amount': payment_data['amount'],
            'status': 'success',
            'ref': payment_data['payment_details']['ref'],
            'bank': payment_data['payment_details']['bank'],
            'buyer': payment_data['payment_details']['buyer']
        }
        db.add_transaction(user_id, transaction)
        
        # Create success message
        t = f'<b>✅ Pembayaran Berhasil!</b>\n\n' \
            f'Jumlah: <b>Rp {payment_data["amount"]:,.0f}</b>\n' \
            f'Saldo Baru: <b>Rp {new_balance:,.0f}</b>\n\n' \
            f'Detail Pembayaran:\n' \
            f'Bank: {payment_data["payment_details"]["bank"]}\n' \
            f'Ref: {payment_data["payment_details"]["ref"]}\n' \
            f'Pembayar: {payment_data["payment_details"]["buyer"]}\n\n' \
            f'Terima kasih atas top up Anda.'
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='📋 Lihat Riwayat',
                callback_data='wallet?nf=show_history'
            )
        )
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali ke Wallet',
                callback_data='wallet?nf=show_wallet'
            )
        )
        
        # Send success notification
        bot.send_message(
            chat_id=user_id,
            text=t,
            reply_markup=markup,
            parse_mode='HTML'
        )
        
        # Update QR message if exists
        if message_id:
            try:
                bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=message_id,
                    caption=f'<b>✅ Pembayaran Berhasil!</b>\n\n'
                           f'Jumlah: <b>Rp {payment_data["amount"]:,.0f}</b>',
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            except:
                pass
                
    except Exception as e:
        bot.send_message(
            chat_id=user_id,
            text=f'❌ Terjadi kesalahan saat memproses pembayaran: {str(e)}'
        )
