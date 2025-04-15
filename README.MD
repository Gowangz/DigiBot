# ☁ `Digitalocean-bot`

![](.README.MD_images/1be8fb97.png)

### 🚚 Telegram Bot untuk Digital Ocean dengan Multi-User dan Auto Order

### 🔖 Fungsi Utama

+ Mengelola akun Digital Ocean, memeriksa saldo akun, dan melakukan pengujian akun dalam batch dengan cepat dan akurat.
+ Membuat dan mengelola mesin virtual dengan mudah dan efisien, memberikan Anda kendali penuh atas infrastruktur cloud Anda.
+ Sistem multi-user dengan pendaftaran pengguna, wallet, dan auto order VPS berdasarkan saldo.
+ Fitur payment gateway (simulasi) untuk top-up saldo secara otomatis.
+ Panel admin untuk mengelola pengguna dan melihat transaksi.

### 🪂 Lingkungan

+ Bot ini dirancang untuk bekerja di berbagai lingkungan, memastikan fleksibilitas dan kompatibilitas yang tinggi.
+ Mendukung mode single-user (hanya admin) atau multi-user sesuai konfigurasi.

### 😻 Tahapan Penggunaan

1. **Clone Proyek**: `git clone` proyek ini ke lokal untuk memulai petualangan Anda.
2. **Instal Ketergantungan**: Jalankan `pip3 install -r requirements.txt` untuk menginstal ketergantungan yang diperlukan dan pastikan semuanya siap.
3. **Buat Bot**: Buat bot baru melalui [@botfather](https://t.me/botfather) dan catat `token` yang diberikan untuk menghubungkan bot Anda.
4. **Edit Konfigurasi**: Edit file `config.json` untuk mengisi konfigurasi yang relevan dengan akun Anda dan sesuaikan dengan kebutuhan Anda.
   ```json
   {
     "BOT": {
       "NAME": "NAMA STORE",
       "TOKEN": "BOT TOKEN",
       "ADMINS": [ID TELEGRAM ADMIN],
       "PAYMENT_CONFIG": {
         "CALLBACK_URL": "https://your-callback-url.com/payment/webhook",
         "USE_SIMULATION": true,
         "CURRENCY": "IDR"
       },
       "MULTI_USER": true
     }
   }
   ```
5. **Jalankan Bot**: Jalankan `python3 main.py` untuk memulai bot dan nikmati kemudahan pengelolaan Digital Ocean Anda dengan antarmuka yang ramah pengguna!

### 📋 Perintah dan Fitur

#### Perintah untuk Semua Pengguna
- `/start` - Memulai bot dan menampilkan menu utama
- `/register` - Mendaftar sebagai pengguna baru
- `/login` - Login ke akun Anda
- `/help` - Menampilkan bantuan

#### Perintah untuk Pengguna Terdaftar
- `/wallet` - Mengelola saldo dan melakukan top-up
- `/topup` - Shortcut untuk menu top-up saldo
- `/auto_order` - Membuat VPS secara otomatis dengan saldo
- `/order` - Shortcut untuk auto_order

#### Perintah untuk Admin
- `/add_do` - Menambahkan akun DigitalOcean
- `/sett_do` - Mengelola akun DigitalOcean
- `/bath_do` - Uji akun batch
- `/add_vps` - Membuat droplet
- `/sett_vps` - Mengelola droplet

### 💵 Alur Auto Order

1. Pengguna mendaftar melalui perintah `/register`
2. Pengguna top-up saldo melalui menu Wallet
3. Setelah saldo mencukupi, pengguna dapat membuat VPS melalui menu Auto Order
4. Sistem mengecek saldo dan mengurangi saldo sesuai harga VPS
5. VPS dibuat dan ditambahkan ke akun pengguna

### 💰 Alur Top-Up Saldo

1. Pengguna memilih menu Wallet
2. Pilih opsi Top-Up dan pilih nominal
3. Pengguna diarahkan untuk melakukan pembayaran
4. Setelah pembayaran berhasil, saldo akan otomatis bertambah

### 💻 Harga VPS (Konfigurasi Default)

- s-1vcpu-1gb: Rp 70.000
- s-1vcpu-2gb: Rp 140.000
- s-2vcpu-2gb: Rp 210.000
- s-2vcpu-4gb: Rp 280.000
- s-4vcpu-8gb: Rp 560.000

### 🛠️ Catatan Pengembangan

- Payment gateway saat ini menggunakan simulasi. Untuk menghubungkan ke payment gateway yang sebenarnya, perbarui modules/payment_gateway.py
- Untuk mengubah harga VPS, edit variabel DROPLET_PRICES di modules/auto_order.py
- Aktifkan atau nonaktifkan mode multi-user melalui konfigurasi "MULTI_USER" di config.json

### 🤖 Identitas Bot

+ **Nama Bot**: DigitalOcean Manager Bot
+ **Deskripsi**: Bot ini membantu Anda mengelola akun DigitalOcean, memeriksa saldo, membuat dan mengelola droplet, serta memberikan informasi detail tentang akun dan droplet Anda. Mendukung fitur multi-user dan auto order.
+ **Versi**: 2.0.0
+ **Bahasa Pemrograman**: Python
+ **Perpustakaan Utama**: `pyTelegramBotAPI`, `digitalocean`, `tinydb`
+ **Lisensi**: MIT License
