import json
import os
from typing import Union
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from _bot import bot
from modules.auth import is_admin

VPS_PRICES_FILE = 'data/vps_prices.json'

def get_vps_specs():
    """Get list of VPS specifications."""
    return {
        's-1vcpu-1gb': '1 vCPU, 1GB RAM',
        's-1vcpu-2gb': '1 vCPU, 2GB RAM',
        's-2vcpu-2gb': '2 vCPU, 2GB RAM',
        's-2vcpu-4gb': '2 vCPU, 4GB RAM',
        's-4vcpu-8gb': '4 vCPU, 8GB RAM'
    }

def load_vps_prices():
    """Load VPS prices from file."""
    try:
        with open(VPS_PRICES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {
            's-1vcpu-1gb': 70000,
            's-1vcpu-2gb': 140000,
            's-2vcpu-2gb': 210000,
            's-2vcpu-4gb': 280000,
            's-4vcpu-8gb': 560000
        }

def save_vps_prices(prices):
    """Save VPS prices to file."""
    os.makedirs(os.path.dirname(VPS_PRICES_FILE), exist_ok=True)
    with open(VPS_PRICES_FILE, 'w') as f:
        json.dump(prices, f, indent=2)

def edit_vps_price(d: Union[Message, CallbackQuery], data: dict = None):
    """Handle VPS price editing."""
    user_id = d.from_user.id
    
    from _bot import config, logger
    logger.info(f"Checking admin access in admin_tools for user {user_id}")
    logger.info(f"Config admins: {config.admins}")
    logger.info(f"Is database admin: {is_admin(user_id)}")
    logger.info(f"User ID type: {type(user_id)}")
    if not (is_admin(user_id) or int(user_id) in config.admins):
        bot.send_message(
            chat_id=user_id,
            text="🚫 Anda tidak memiliki izin untuk menggunakan fitur ini."
        )
        return

    if isinstance(d, Message):
        show_vps_prices(d)
        return

    if not data:
        show_vps_prices(d)
        return

    next_func = data.get('nf', ['show'])[0]
    
    if next_func == 'show':
        show_vps_prices(d)
    elif next_func == 'edit':
        spec = data.get('spec', [None])[0]
        if spec:
            ask_new_price(d, spec)

def show_vps_prices(d: Union[Message, CallbackQuery]):
    """Show current VPS prices."""
    prices = load_vps_prices()
    specs = get_vps_specs()
    
    text = "<b>💰 Daftar Harga VPS</b>\n\n"
    for spec, desc in specs.items():
        price = prices.get(spec, 0)
        text += f"📌 <code>{spec}</code>\n"
        text += f"💻 {desc}\n"
        text += f"💵 Rp {price:,}\n\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    for spec in specs.keys():
        markup.add(
            InlineKeyboardButton(
                text=f"Edit {spec}",
                callback_data=f"admin_tools?nf=edit&spec={spec}"
            )
        )
    
    markup.row(
        InlineKeyboardButton(
            text="⬅️ Kembali",
            callback_data="start"
        )
    )

    if isinstance(d, Message):
        bot.send_message(
            chat_id=d.from_user.id,
            text=text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    else:
        try:
            bot.edit_message_text(
                chat_id=d.from_user.id,
                message_id=d.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                chat_id=d.from_user.id,
                text=text,
                reply_markup=markup,
                parse_mode='HTML'
            )

def ask_new_price(call: CallbackQuery, spec: str):
    """Ask admin for new price."""
    prices = load_vps_prices()
    specs = get_vps_specs()
    current_price = prices.get(spec, 0)
    
    text = f"<b>💰 Edit Harga VPS</b>\n\n"
    text += f"📌 Spesifikasi: <code>{spec}</code>\n"
    text += f"💻 {specs.get(spec, '')}\n"
    text += f"💵 Harga Saat Ini: Rp {current_price:,}\n\n"
    text += "Balas dengan harga baru (dalam Rupiah)\n"
    text += "Contoh: 100000"
    
    msg = bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=text,
        parse_mode='HTML'
    )
    
    bot.register_next_step_handler(msg, save_new_price, spec)

def save_new_price(message: Message, spec: str):
    """Save new price for VPS specification."""
    try:
        new_price = int(message.text.strip().replace(',', ''))
        if new_price <= 0:
            raise ValueError()
            
        prices = load_vps_prices()
        old_price = prices.get(spec, 0)
        prices[spec] = new_price
        save_vps_prices(prices)
        
        text = "<b>✅ Harga berhasil diperbarui!</b>\n\n"
        text += f"📌 Spesifikasi: <code>{spec}</code>\n"
        text += f"💻 {get_vps_specs().get(spec, '')}\n"
        text += f"💵 Harga Lama: Rp {old_price:,}\n"
        text += f"💵 Harga Baru: Rp {new_price:,}"
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text="⬅️ Kembali ke Daftar Harga",
                callback_data="admin_tools?nf=show"
            )
        )
        
        bot.send_message(
            chat_id=message.from_user.id,
            text=text,
            reply_markup=markup,
            parse_mode='HTML'
        )
        
    except ValueError:
        text = "❌ Input tidak valid! Masukkan angka yang benar.\n"
        text += "Contoh: 100000"
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton(
                text="⬅️ Kembali ke Daftar Harga",
                callback_data="admin_tools?nf=show"
            )
        )
        
        bot.send_message(
            chat_id=message.from_user.id,
            text=text,
            reply_markup=markup
        )
