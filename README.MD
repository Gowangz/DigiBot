# DigiBot - DigitalOcean VPS Management Bot

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

---

## English

A robust Telegram bot for managing DigitalOcean VPS instances with an integrated wallet, QRIS payment system, and multi-user support.

### Features

#### User Features
- 💰 **Wallet System**: Check balance, top up via QRIS, and view transaction history.
- 🖥️ **VPS Management**: Auto-order VPS with multiple specifications and monitor status in real-time.

#### Admin Features
- 👥 **User Management**: View registered users, manage permissions, and monitor transactions.
- 🔧 **DigitalOcean Integration**: Add/manage DO accounts, create droplets, monitor status, and batch test accounts.
- 💲 **Price Management**: Set and update VPS prices with dynamic pricing support.

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- DigitalOcean API Key
- QRIS Payment Gateway Account

### Installation & Running

1. Clone the repository:
   ```bash
   git clone https://github.com/Gowangz/DigiBot.git
   cd DigiBot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the bot:
   - Copy `config.example.json` to `config.json`:
     ```bash
     cp config.example.json config.json
     ```
   - Edit `config.json` with your bot token, admin Telegram IDs, and payment gateway configuration.
4. Run the bot:
   ```bash
   python main.py
   ```

---

## Bahasa Indonesia

Bot Telegram handal untuk mengelola instance VPS DigitalOcean dengan sistem dompet terintegrasi, pembayaran QRIS, dan dukungan multi-pengguna.

### Fitur

#### Fitur Pengguna
- 💰 **Sistem Dompet**: Cek saldo, top-up otomatis via QRIS, dan riwayat transaksi.
- 🖥️ **Manajemen VPS**: Order VPS otomatis dengan berbagai pilihan spesifikasi dan pemantauan status real-time.

#### Fitur Admin
- 👥 **Manajemen Pengguna**: Lihat daftar pengguna terdaftar, kelola hak akses, dan pantau transaksi.
- 🔧 **Integrasi DigitalOcean**: Tambah/kelola akun DO, buat droplet, pantau status, dan tes akun secara batch.
- 💲 **Manajemen Harga**: Atur dan perbarui harga VPS dengan dukungan harga dinamis.

### Prasyarat
- Python 3.8+
- Token Bot Telegram dari BotFather
- API Key DigitalOcean
- Akun Payment Gateway QRIS

### Instalasi & Cara Menjalankan

1. Clone repository:
   ```bash
   git clone https://github.com/Gowangz/DigiBot.git
   cd DigiBot
   ```
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Konfigurasi bot:
   - Salin file `config.example.json` menjadi `config.json`:
     ```bash
     cp config.example.json config.json
     ```
   - Sesuaikan isi `config.json` dengan token bot, ID Telegram admin, serta kredensial gateway pembayaran Anda.
4. Jalankan bot:
   ```bash
   python main.py
   ```

## License / Lisensi
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. / Proyek ini dilisensikan di bawah Lisensi MIT - lihat file [LICENSE](LICENSE) untuk detail.
