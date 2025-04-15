from typing import Union

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import digitalocean

from _bot import bot
from utils.db import AccountsDB
from utils.multiuser_db import UsersDB, UserDropletsDB
from modules.register import check_auth


def user_droplets(d: Union[Message, CallbackQuery], data: dict = None):
    """Handle menu droplet pengguna."""
    data = data or {}
    next_func = data.get('nf', ['show_droplets'])[0]
    
    # Periksa autentikasi pengguna
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


def show_droplets(d: Union[Message, CallbackQuery], data: dict = None):
    """Menampilkan daftar droplet milik pengguna."""
    user_id = d.from_user.id
    
    # Ambil daftar droplet pengguna
    user_droplets = UserDropletsDB().get_by_user(user_id)
    
    if not user_droplets:
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='🚀 Order VPS Baru',
                callback_data='auto_order?nf=select_account'
            )
        )
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali ke Menu',
                callback_data='start'
            )
        )
        
        msg = '🔍 <b>VPS Saya</b>\n\n' \
              'Anda belum memiliki VPS.\n' \
              'Silakan lakukan order untuk membuat VPS baru.'
        
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
        return
    
    # Siapkan pesan
    msg = '🔍 <b>VPS Saya</b>\n\n'
    
    # Siapkan markup
    markup = InlineKeyboardMarkup()
    
    # Ambil detail masing-masing droplet
    for item in user_droplets:
        account_doc_id = item.get('account_doc_id')
        droplet_id = item.get('droplet_id')
        
        account = AccountsDB().get(doc_id=account_doc_id)
        if not account:
            continue
        
        try:
            # Ambil informasi droplet dari DigitalOcean API
            droplet = digitalocean.Droplet.get_object(
                api_token=account['token'],
                droplet_id=droplet_id
            )
            
            # Tambahkan ke pesan
            status_emoji = '🟢' if droplet.status == 'active' else '🔴'
            msg += f'{status_emoji} <b>{droplet.name}</b>\n' \
                   f'IP: <code>{droplet.ip_address}</code>\n' \
                   f'Status: {droplet.status}\n' \
                   f'Region: {droplet.region["name"]}\n' \
                   f'Size: {droplet.size_slug}\n\n'
            
            # Tambahkan tombol aksi
            markup.add(
                InlineKeyboardButton(
                    text=f'🔧 {droplet.name}',
                    callback_data=f'user_droplet_action?doc_id={account_doc_id}&droplet_id={droplet_id}'
                )
            )
            
        except Exception:
            # Jika gagal mengambil detail droplet, tampilkan pesan sederhana
            msg += f'❓ <b>Droplet #{droplet_id}</b>\n' \
                   f'Status: Tidak dapat mengambil detail\n\n'
    
    # Tambahkan tombol kembali dan order baru
    markup.row(
        InlineKeyboardButton(
            text='🚀 Order VPS Baru',
            callback_data='auto_order?nf=select_account'
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


def user_droplet_action(call: CallbackQuery, data: dict):
    """Menampilkan menu aksi untuk droplet pengguna."""
    user_id = call.from_user.id
    doc_id = int(data.get('doc_id', [0])[0])
    droplet_id = int(data.get('droplet_id', [0])[0])
    
    account = AccountsDB().get(doc_id=doc_id)
    if not account:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Akun tidak ditemukan',
            show_alert=True
        )
        return
    
    try:
        # Ambil informasi droplet dari DigitalOcean API
        droplet = digitalocean.Droplet.get_object(
            api_token=account['token'],
            droplet_id=droplet_id
        )
        
        # Siapkan pesan
        msg = f'🔧 <b>Aksi untuk {droplet.name}</b>\n\n' \
              f'IP: <code>{droplet.ip_address}</code>\n' \
              f'Status: {droplet.status}\n' \
              f'Region: {droplet.region["name"]}\n' \
              f'Size: {droplet.size_slug}\n' \
              f'Disk: {droplet.disk} GB\n' \
              f'Memory: {droplet.memory} MB\n' \
              f'vCPU: {droplet.vcpus}\n\n' \
              f'Silakan pilih aksi untuk droplet ini:'
        
        # Siapkan markup berdasarkan status droplet
        markup = InlineKeyboardMarkup(row_width=2)
        
        if droplet.status == 'active':
            markup.add(
                InlineKeyboardButton(
                    text='🔄 Reboot',
                    callback_data=f'user_droplet_control?action=reboot&doc_id={doc_id}&droplet_id={droplet_id}'
                ),
                InlineKeyboardButton(
                    text='⏸️ Power Off',
                    callback_data=f'user_droplet_control?action=power_off&doc_id={doc_id}&droplet_id={droplet_id}'
                )
            )
        elif droplet.status == 'off':
            markup.add(
                InlineKeyboardButton(
                    text='▶️ Power On',
                    callback_data=f'user_droplet_control?action=power_on&doc_id={doc_id}&droplet_id={droplet_id}'
                )
            )
        
        # Tombol hapus selalu tersedia
        markup.row(
            InlineKeyboardButton(
                text='❌ Hapus VPS',
                callback_data=f'user_droplet_control?action=delete&doc_id={doc_id}&droplet_id={droplet_id}'
            )
        )
        
        # Tombol kembali
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali',
                callback_data='user_droplets?nf=show_droplets'
            )
        )
        
        # Kirim pesan
        bot.edit_message_text(
            text=msg,
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
        
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'❌ Gagal mengambil detail droplet: {str(e)}',
            show_alert=True
        )


def user_droplet_control(call: CallbackQuery, data: dict):
    """Menangani aksi kontrol droplet pengguna."""
    user_id = call.from_user.id
    action = data.get('action', [''])[0]
    doc_id = int(data.get('doc_id', [0])[0])
    droplet_id = int(data.get('droplet_id', [0])[0])
    
    account = AccountsDB().get(doc_id=doc_id)
    if not account:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Akun tidak ditemukan',
            show_alert=True
        )
        return
    
    # Periksa apakah droplet milik pengguna ini
    user_droplet = UserDropletsDB().get_droplet(user_id, droplet_id)
    if not user_droplet:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ VPS ini bukan milik Anda',
            show_alert=True
        )
        return
    
    try:
        droplet = digitalocean.Droplet.get_object(
            api_token=account['token'],
            droplet_id=droplet_id
        )
        
        # Jalankan aksi berdasarkan permintaan
        if action == 'reboot':
            # Reboot droplet
            droplet.reboot()
            action_name = 'Reboot'
            success_msg = 'VPS sedang direstart.'
        
        elif action == 'power_off':
            # Power off droplet
            droplet.power_off()
            action_name = 'Power Off'
            success_msg = 'VPS dimatikan.'
        
        elif action == 'power_on':
            # Power on droplet
            droplet.power_on()
            action_name = 'Power On'
            success_msg = 'VPS dinyalakan.'
        
        elif action == 'delete':
            # Konfirmasi penghapusan
            msg = f'⚠️ <b>Konfirmasi Penghapusan</b>\n\n' \
                  f'Anda akan menghapus VPS: <b>{droplet.name}</b>\n' \
                  f'IP: <code>{droplet.ip_address}</code>\n\n' \
                  f'Aksi ini TIDAK DAPAT DIBATALKAN dan semua data akan hilang.\n\n' \
                  f'Apakah Anda yakin?'
            
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton(
                    text='✅ Ya, Hapus',
                    callback_data=f'user_droplet_confirm_delete?doc_id={doc_id}&droplet_id={droplet_id}'
                ),
                InlineKeyboardButton(
                    text='❌ Tidak, Batal',
                    callback_data=f'user_droplet_action?doc_id={doc_id}&droplet_id={droplet_id}'
                )
            )
            
            bot.edit_message_text(
                text=msg,
                chat_id=user_id,
                message_id=call.message.message_id,
                parse_mode='HTML',
                reply_markup=markup
            )
            return
        
        else:
            # Aksi tidak valid
            bot.answer_callback_query(
                callback_query_id=call.id,
                text='❌ Aksi tidak valid',
                show_alert=True
            )
            return
        
        # Notifikasi sukses
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'✅ {action_name} berhasil: {success_msg}',
            show_alert=True
        )
        
        # Kembali ke daftar droplet
        show_droplets(call)
        
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'❌ Gagal melakukan aksi: {str(e)}',
            show_alert=True
        )


def user_droplet_confirm_delete(call: CallbackQuery, data: dict):
    """Konfirmasi dan jalankan penghapusan droplet."""
    user_id = call.from_user.id
    doc_id = int(data.get('doc_id', [0])[0])
    droplet_id = int(data.get('droplet_id', [0])[0])
    
    account = AccountsDB().get(doc_id=doc_id)
    if not account:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ Akun tidak ditemukan',
            show_alert=True
        )
        return
    
    # Periksa apakah droplet milik pengguna ini
    user_droplet = UserDropletsDB().get_droplet(user_id, droplet_id)
    if not user_droplet:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text='❌ VPS ini bukan milik Anda',
            show_alert=True
        )
        return
    
    try:
        # Ambil informasi droplet sebelum dihapus
        droplet = digitalocean.Droplet.get_object(
            api_token=account['token'],
            droplet_id=droplet_id
        )
        droplet_name = droplet.name
        
        # Hapus droplet
        droplet.destroy()
        
        # Hapus dari database pengguna
        UserDropletsDB().remove(user_id, droplet_id)
        
        # Notifikasi sukses
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'✅ VPS {droplet_name} berhasil dihapus',
            show_alert=True
        )
        
        # Kembali ke daftar droplet
        show_droplets(call)
        
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'❌ Gagal menghapus VPS: {str(e)}',
            show_alert=True
        )
