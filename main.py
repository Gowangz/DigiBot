def parse_config():
    import json
    from os import environ

    config = json.load(open('config.json', 'r', encoding='utf-8'))
    environ['bot_name'] = config['BOT']['NAME']
    environ['bot_token'] = config['BOT']['TOKEN']
    environ['bot_admins'] = json.dumps(config['BOT']['ADMINS'])
    environ['multi_user'] = str(config['BOT'].get('MULTI_USER', False))
    
    # Payment gateway configuration
    payment_config = config['BOT'].get('PAYMENT_CONFIG', {})
    environ['payment_callback_url'] = payment_config.get('CALLBACK_URL', '')
    environ['payment_use_simulation'] = str(payment_config.get('USE_SIMULATION', True))
    environ['payment_currency'] = payment_config.get('CURRENCY', 'IDR')


def setup_database():
    """Memastikan database dipersiapkan dengan benar."""
    import os
    from tinydb import TinyDB
    
    # Pastikan file database ada
    db_path = 'db.json'
    if not os.path.exists(db_path):
        TinyDB(db_path)
    
    # Memastikan tabel-tabel yang diperlukan sudah ada
    db = TinyDB(db_path)
    if 'Accounts' not in db.tables():
        db.table('Accounts')
    if 'Users' not in db.tables():
        db.table('Users')
    if 'Transactions' not in db.tables():
        db.table('Transactions')
    if 'UserDroplets' not in db.tables():
        db.table('UserDroplets')


def start_bot():
    from bot import bot

    bot.polling(none_stop=True)


if __name__ == '__main__':
    parse_config()
    setup_database()
    start_bot()
