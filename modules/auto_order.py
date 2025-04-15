from typing import Union
from time import sleep

from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import digitalocean

from _bot import bot
from utils.db import AccountsDB
from utils.multiuser_db import UsersDB, TransactionsDB, UserDropletsDB
from utils.localizer import localize_region
from utils.set_root_password_script import set_root_password_script
from utils.password_generator import password_generator
from modules.register import check_auth
from modules.wallet import show_wallet

# Harga tier (dalam rupiah)
DROPLET_PRICES = {
    's-1vcpu-1gb': 70000,
    's-1vcpu-2gb': 140000,
    's-2vcpu-2gb': 210000,
    's-2vcpu-4gb': 280000,
    's-4vcpu-8gb': 560000,
}

# Data sementara untuk auto order
auto_order_dict = {}

t = '<b>🤖 Auto Order VPS</b>\n\n'


def auto_order(d: Union[Message, CallbackQuery], data: dict = None):
    """Handle auto order."""
    data = data or {}
    next_func = data.get('nf', ['select_account'])[0]
    
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


def select_account(d: Union[Message, CallbackQuery]):
    """Pilih akun DigitalOcean untuk auto order."""
    accounts = AccountsDB().all()
    
    if not accounts:
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali ke Menu',
                callback_data='start'
            )
        )
        
        bot.send_message(
            text=f'{t}'
                 '⚠️ Tidak ada akun DigitalOcean yang tersedia. Silakan hubungi admin.',
            chat_id=d.from_user.id,
            parse_mode='HTML',
            reply_markup=markup
        )
        return
    
    # Buat markup
    markup = InlineKeyboardMarkup()
    for account in accounts:
        markup.add(
            InlineKeyboardButton(
                text=account['email'],
                callback_data=f'auto_order?nf=select_region&doc_id={account.doc_id}'
            )
        )
    
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali ke Menu',
            callback_data='start'
        )
    )
    
    # Kirim pesan
    bot.send_message(
        text=f'{t}'
             '👤 Pilih Akun DigitalOcean',
        chat_id=d.from_user.id,
        parse_mode='HTML',
        reply_markup=markup
    )


def select_region(call: CallbackQuery, data: dict):
    """Pilih region untuk auto order."""
    doc_id = data['doc_id'][0]
    user_id = call.from_user.id

    account = AccountsDB().get(doc_id=doc_id)
    auto_order_dict[user_id] = {
        'account': account
    }

    _t = t + f'👤 Akun: <code>{account["email"]}</code>\n\n'

    bot.edit_message_text(
        text=f'{_t}'
             f'🌍 Mengambil daftar Wilayah...',
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )

    try:
        regions = digitalocean.Manager(token=account['token']).get_all_regions()
    except Exception as e:
        bot.edit_message_text(
            text=f'{_t}'
                 '⚠️ Kesalahan saat mengambil Wilayah: '
                 f'<code>{str(e)}</code>',
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        return

    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for region in regions:
        if region.available:
            buttons.append(
                InlineKeyboardButton(
                    text=localize_region(slug=region.slug),
                    callback_data=f'auto_order?nf=select_size&region={region.slug}'
                )
            )
    markup.add(*buttons)
    
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data='auto_order?nf=select_account'
        )
    )

    bot.edit_message_text(
        text=f'{_t}'
             f'🌍 Pilih Wilayah',
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='HTML'
    )


def select_size(call: CallbackQuery, data: dict):
    """Pilih ukuran droplet untuk auto order."""
    region_slug = data['region'][0]
    user_id = call.from_user.id

    auto_order_dict[user_id].update({
        'region_slug': region_slug
    })

    _t = t + f'👤 Akun: <code>{auto_order_dict[user_id]["account"]["email"]}</code>\n' \
             f'🌍 Wilayah: <code>{region_slug}</code>\n\n'

    bot.edit_message_text(
        text=f'{_t}'
             f'📏 Mengambil daftar Ukuran...',
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )

    try:
        sizes = digitalocean.Manager(token=auto_order_dict[user_id]['account']['token']).get_all_sizes()
    except Exception as e:
        bot.edit_message_text(
            text=f'{_t}'
                 '⚠️ Kesalahan saat mengambil Ukuran: '
                 f'<code>{str(e)}</code>',
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        return

    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    user_data = UsersDB().get_by_id(user_id)
    balance = user_data.get('balance', 0)
    
    for size in sizes:
        if region_slug in size.regions and size.slug in DROPLET_PRICES:
            price = DROPLET_PRICES[size.slug]
            if balance >= price:
                label = f"{size.slug} - Rp {price:,}"
            else:
                label = f"{size.slug} - Rp {price:,} ❌"
                
            buttons.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f'auto_order?nf=check_balance&size={size.slug}'
                )
            )
            
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data=f'auto_order?nf=select_region&doc_id={auto_order_dict[user_id]["account"].doc_id}'
        )
    )

    bot.edit_message_text(
        text=f'{_t}'
             f'📏 Pilih Ukuran VPS\n'
             f'💰 Saldo Anda: <b>Rp {balance:,}</b>',
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='HTML'
    )


def check_balance(call: CallbackQuery, data: dict):
    """Periksa saldo pengguna sebelum melanjutkan pemilihan OS."""
    size_slug = data['size'][0]
    user_id = call.from_user.id

    # Update data pesanan
    auto_order_dict[user_id].update({
        'size_slug': size_slug
    })

    _t = t + f'👤 Akun: <code>{auto_order_dict[user_id]["account"]["email"]}</code>\n' \
             f'🌍 Wilayah: <code>{auto_order_dict[user_id]["region_slug"]}</code>\n' \
             f'📏 Ukuran: <code>{size_slug}</code>\n\n'

    # Periksa saldo
    user_data = UsersDB().get_by_id(user_id)
    balance = user_data.get('balance', 0)
    
    # Hitung harga VPS
    if size_slug in DROPLET_PRICES:
        price = DROPLET_PRICES[size_slug]
    else:
        # Jika ukuran tidak ada dalam daftar harga, gunakan harga default
        price = 70000  # Harga default untuk size yang tidak dikenal
    
    # Simpan harga untuk digunakan nanti
    auto_order_dict[user_id]['price'] = price
    
    if balance < price:
        # Saldo tidak mencukupi
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                text='💰 Top Up Saldo',
                callback_data='wallet?nf=topup_options'
            ),
            InlineKeyboardButton(
                text='⬅️ Kembali',
                callback_data=f'auto_order?nf=select_size&region={auto_order_dict[user_id]["region_slug"]}'
            )
        )
        
        bot.edit_message_text(
            text=f'{_t}'
                 f'❌ Saldo Anda tidak mencukupi untuk order ini.\n\n'
                 f'💰 Saldo Anda: <b>Rp {balance:,}</b>\n'
                 f'💵 Harga VPS: <b>Rp {price:,}</b>\n'
                 f'🔢 Kurang: <b>Rp {price - balance:,}</b>\n\n'
                 f'Silakan top up saldo Anda terlebih dahulu.',
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        return
    
    # Lanjut ke pemilihan OS
    select_os(call, {})


def select_os(d: Union[Message, CallbackQuery], data: dict):
    """Pilih OS untuk auto order."""
    user_id = d.from_user.id

    _t = t + f'👤 Akun: <code>{auto_order_dict[user_id]["account"]["email"]}</code>\n' \
             f'🌍 Wilayah: <code>{auto_order_dict[user_id]["region_slug"]}</code>\n' \
             f'📏 Ukuran: <code>{auto_order_dict[user_id]["size_slug"]}</code>\n\n'

    def get_os_markup():
        try:
            images = digitalocean.Manager(token=auto_order_dict[user_id]['account']['token']).get_distro_images()
        except Exception as e:
            bot.edit_message_text(
                text=f'{_t}'
                     '⚠️ Kesalahan saat mengambil OS: '
                     f'<code>{str(e)}</code>',
                chat_id=user_id,
                message_id=d.message.message_id,
                parse_mode='HTML'
            )
            return InlineKeyboardMarkup()

        markup = InlineKeyboardMarkup(row_width=2)
        buttons = []
        for image in images:
            if image.distribution in ['Ubuntu', 'CentOS', 'Debian'] \
                    and image.public \
                    and image.status == 'available' \
                    and auto_order_dict[user_id]["region_slug"] in image.regions:
                buttons.append(
                    InlineKeyboardButton(
                        text=f'{image.distribution} {image.name}',
                        callback_data=f'auto_order?nf=get_name&image={image.slug}'
                    )
                )
        markup.add(*buttons)
        markup.row(
            InlineKeyboardButton(
                text='⬅️ Kembali',
                callback_data=f'auto_order?nf=select_size&region={auto_order_dict[user_id]["region_slug"]}'
            )
        )

        return markup

    if isinstance(d, Message):
        msg = bot.send_message(
            text=f'{_t}'
                 f'🖼️ Mengambil daftar OS...',
            chat_id=user_id,
            parse_mode='HTML'
        )
        bot.edit_message_text(
            text=f'{_t}'
                 f'🖼️ Pilih OS',
            chat_id=user_id,
            message_id=msg.message_id,
            reply_markup=get_os_markup(),
            parse_mode='HTML'
        )

    elif isinstance(d, CallbackQuery):
        bot.edit_message_text(
            text=f'{_t}'
                 f'🖼️ Mengambil daftar OS...',
            chat_id=user_id,
            message_id=d.message.message_id,
            parse_mode='HTML'
        )
        bot.edit_message_text(
            text=f'{_t}'
                 f'🖼️ Pilih OS',
            chat_id=user_id,
            message_id=d.message.message_id,
            reply_markup=get_os_markup(),
            parse_mode='HTML'
        )


def get_name(call: CallbackQuery, data: dict):
    """Dapatkan nama droplet untuk auto order."""
    image_slug = data['image'][0]
    user_id = call.from_user.id

    auto_order_dict[user_id].update({
        'image_slug': image_slug
    })

    _t = t + f'👤 Akun: <code>{auto_order_dict[user_id]["account"]["email"]}</code>\n' \
             f'🌍 Wilayah: <code>{auto_order_dict[user_id]["region_slug"]}</code>\n' \
             f'📏 Ukuran: <code>{auto_order_dict[user_id]["size_slug"]}</code>\n' \
             f'🖼️ OS: <code>{image_slug}</code>\n\n'

    msg = bot.edit_message_text(
        text=f'{_t}'
             '📝 Harap balas dengan Nama Instance, contoh: FighterTunnel\n\n'
             '/cancel untuk membatalkan',
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, ask_create)


def ask_create(m: Message):
    """Konfirmasi pembuatan droplet."""
    user_id = m.from_user.id
    
    if m.text == '/cancel':
        select_os(m, {})
        return

    auto_order_dict[user_id].update({
        'droplet_name': m.text
    })

    _t = t + f'👤 Akun: <code>{auto_order_dict[user_id]["account"]["email"]}</code>\n' \
             f'🌍 Wilayah: <code>{auto_order_dict[user_id]["region_slug"]}</code>\n' \
             f'📏 Ukuran: <code>{auto_order_dict[user_id]["size_slug"]}</code>\n' \
             f'🖼️ OS: <code>{auto_order_dict[user_id]["image_slug"]}</code>\n' \
             f'📝 Nama: <code>{m.text}</code>\n\n'
    
    # Ambil informasi harga
    price = auto_order_dict[user_id].get('price', 0)
    
    # Ambil informasi saldo
    user_data = UsersDB().get_by_id(user_id)
    balance = user_data.get('balance', 0)
    
    _t += f'💰 Saldo Anda: <b>Rp {balance:,}</b>\n' \
          f'💵 Harga VPS: <b>Rp {price:,}</b>\n' \
          f'💰 Sisa Saldo: <b>Rp {balance - price:,}</b>\n\n'
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(
            text='⬅️ Kembali',
            callback_data=f'auto_order?nf=get_name&image={auto_order_dict[user_id]["image_slug"]}'
        ),
        InlineKeyboardButton(
            text='❌ Batal',
            callback_data='auto_order?nf=cancel_create'
        ),
    )
    markup.row(
        InlineKeyboardButton(
            text='✅ Buat VPS',
            callback_data=f'auto_order?nf=confirm_create'
        )
    )

    bot.send_message(
        text=_t,
        chat_id=user_id,
        reply_markup=markup,
        parse_mode='HTML'
    )


def cancel_create(call: CallbackQuery):
    """Batalkan pembuatan droplet."""
    bot.edit_message_text(
        text=f'{call.message.html_text}\n\n'
             '<b>❌ Membatalkan</b>',
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )


def confirm_create(call: CallbackQuery):
    """Konfirmasi dan proses pembuatan droplet."""
    user_id = call.from_user.id
    
    # Periksa kembali saldo untuk memastikan masih cukup
    user_data = UsersDB().get_by_id(user_id)
    balance = user_data.get('balance', 0)
    price = auto_order_dict[user_id].get('price', 0)
    
    if balance < price:
        bot.edit_message_text(
            text=f'{call.message.html_text}\n\n'
                 '<b>❌ Saldo tidak mencukupi. Silakan top up terlebih dahulu.</b>',
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        return
    
    # Kurangi saldo
    try:
        UsersDB().update_balance(user_id, -price)
        
        # Tambahkan transaksi
        TransactionsDB().add(
            user_id=user_id,
            amount=-price,
            type_='purchase',
            details=f"VPS {auto_order_dict[user_id]['size_slug']} - {auto_order_dict[user_id]['droplet_name']}"
        )
    except Exception as e:
        bot.edit_message_text(
            text=f'{call.message.html_text}\n\n'
                 f'<b>❌ Gagal memproses pembayaran: {str(e)}</b>',
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        return
    
    # Buat droplet
    bot.edit_message_text(
        text=f'{call.message.html_text}\n\n'
             '<b>🔄 Membuat VPS...</b>',
        chat_id=user_id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
    
    try:
        password = password_generator()
        
        droplet = digitalocean.Droplet(
            token=auto_order_dict[user_id]['account']['token'],
            name=auto_order_dict[user_id]['droplet_name'],
            region=auto_order_dict[user_id]['region_slug'],
            image=auto_order_dict[user_id]['image_slug'],
            size_slug=auto_order_dict[user_id]['size_slug'],
            user_data=set_root_password_script(password)
        )
        droplet.create()

        droplet_actions = droplet.get_actions()
        for action in droplet_actions:
            while action.status != 'completed':
                sleep(3)
                action.load()
        droplet.load()

        # Menunggu IP address siap
        while not droplet.ip_address:
            sleep(3)
            droplet.load()
            
        # Simpan droplet ke database pengguna
        UserDropletsDB().add(
            user_id=user_id,
            doc_id=auto_order_dict[user_id]['account'].doc_id,
            droplet_id=droplet.id
        )
        
    except Exception as e:
        # Jika terjadi kesalahan, kembalikan saldo
        UsersDB().update_balance(user_id, price)
        
        # Tambahkan transaksi pengembalian
        TransactionsDB().add(
            user_id=user_id,
            amount=price,
            type_='refund',
            details=f"Refund: Gagal membuat VPS - {str(e)}"
        )
        
        bot.edit_message_text(
            text=f'{call.message.html_text}\n\n'
                 f'<b>❌ Gagal membuat VPS: {str(e)}</b>\n'
                 f'Saldo telah dikembalikan.',
            chat_id=user_id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            text='🔍 Lihat Detail',
            callback_data=f'droplet_detail?'
                          f'doc_id={auto_order_dict[user_id]["account"].doc_id}&'
                          f'droplet_id={droplet.id}'
        )
    )
    markup.row(
        InlineKeyboardButton(
            text='⬅️ Kembali ke Menu',
            callback_data='start'
        )
    )

    # Kirim informasi VPS yang berhasil dibuat
    bot.edit_message_text(
        text=f'{call.message.html_text}\n'
             f'🌐 IP: <code>{droplet.ip_address}</code>\n'
             f'🔑 Password: <code>{password}</code>\n\n'
             '<b>✅ VPS berhasil dibuat!</b>',
        chat_id=user_id,
        reply_markup=markup,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )
