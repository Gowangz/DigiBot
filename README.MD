# DigiBot - Digital Ocean VPS Management Bot

A Telegram bot for managing DigitalOcean VPS instances with integrated payment system and multi-user support.

## Features

### User Features
- 💰 Wallet System
  - Check balance
  - Top up via QRIS
  - Transaction history

- 🖥️ VPS Management
  - Auto order VPS
  - Multiple VPS specifications available
  - Real-time VPS status monitoring

### Admin Features
- 👥 User Management
  - View registered users
  - Manage user permissions
  - Monitor user transactions

- 🔧 DigitalOcean Integration
  - Add/manage DO accounts
  - Create droplets
  - Monitor droplet status
  - Batch test accounts

- 💲 Price Management
  - Set VPS prices
  - Dynamic pricing support
  - Price history tracking

## Setup

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- DigitalOcean API Key
- QRIS Payment Gateway Account

### Installation

1. Clone the repository
```bash
git clone https://github.com/Gowangz/DigiBot.git
cd DigiBot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure the bot
- Copy `config.example.json` to `config.json`
- Update the configuration:
  ```json
  {
    "BOT": {
      "NAME": "DigiBot",
      "TOKEN": "YOUR_BOT_TOKEN",
      "ADMINS": ["YOUR_TELEGRAM_ID"],
      "MULTI_USER": true,
      "PAYMENT_CONFIG": {
        "CALLBACK_URL": "YOUR_CALLBACK_URL",
        "USE_SIMULATION": false,
        "CURRENCY": "IDR",
        "DATA_QRIS": "YOUR_QRIS_DATA",
        "MERCHANT_ID": "YOUR_MERCHANT_ID",
        "API_KEY": "YOUR_API_KEY",
        "CHECK_INTERVAL": 5,
        "EXPIRE_TIME": 30
      }
    }
  }
  ```

4. Run the bot
```bash
python main.py
```

## Bot Commands

### Public Commands
- `/start` - Start the bot
- `/register` - Register new account
- `/login` - Login to existing account
- `/help` - Show help message

### User Commands
- `/wallet` - Check wallet balance and top up
- `/topup` - Top up wallet via QRIS
- `/order` - Order new VPS
- `/auto_order` - Automatic VPS ordering

### Admin Commands
- `/add_do` - Add DigitalOcean account
- `/sett_do` - Manage DO accounts
- `/bath_do` - Batch test DO accounts
- `/add_vps` - Create new droplet
- `/sett_vps` - Manage droplets
- `/edit_vps_price` - Edit VPS prices

## Project Structure
```
DigiBot/
├── bot.py              # Main bot logic
├── _bot.py            # Bot configuration
├── main.py            # Entry point
├── config.json        # Configuration file
├── requirements.txt   # Python dependencies
├── data/             # Data storage
│   └── vps_prices.json
└── modules/          # Bot modules
    ├── __init__.py
    ├── admin_tools.py
    ├── auth.py
    ├── auto_order.py
    ├── payment_gateway.py
    ├── register.py
    ├── start.py
    └── wallet.py
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
For support, please contact [@zotanet](https://t.me/zotanet) on Telegram.
