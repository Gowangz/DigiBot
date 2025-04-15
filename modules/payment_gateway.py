import time
import random
import json
from os import path
from datetime import datetime, timedelta

# Menyimpan informasi pembayaran dalam file simulasi
PAYMENT_STORE_FILE = 'payment_simulation.json'


def load_payments():
    """Load pembayaran dari file simulasi."""
    if not path.exists(PAYMENT_STORE_FILE):
        return {}
    
    try:
        with open(PAYMENT_STORE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_payments(payments):
    """Simpan pembayaran ke file simulasi."""
    with open(PAYMENT_STORE_FILE, 'w') as f:
        json.dump(payments, f, indent=2)


def initiate_payment(user_id, amount, reference_id):
    """
    Simulasi inisiasi pembayaran.
    
    :param user_id: ID pengguna
    :param amount: Jumlah pembayaran
    :param reference_id: ID Referensi transaksi
    :return: (URL pembayaran, status)
    """
    # Load data pembayaran
    payments = load_payments()
    
    # Buat entri baru
    payment_data = {
        'user_id': user_id,
        'amount': amount,
        'reference_id': reference_id,
        'status': 'pending',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'paid_at': None,
        'expire_at': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Simpan ke data pembayaran
    payments[reference_id] = payment_data
    save_payments(payments)
    
    # Buat URL pembayaran simulasi
    # Dalam implementasi nyata, ini akan menjadi URL ke payment gateway
    payment_url = f"https://payment.example.com/pay/{reference_id}"
    
    return payment_url, True


def check_payment_status(reference_id):
    """
    Memeriksa status pembayaran.
    
    Dalam simulasi ini, ada 3 kemungkinan:
    1. Pembayaran sudah selesai (completed)
    2. Pembayaran masih tertunda (pending)
    3. Pembayaran gagal atau tidak ditemukan (failed)
    
    :param reference_id: ID Referensi pembayaran
    :return: (status, amount)
    """
    # Load data pembayaran
    payments = load_payments()
    
    # Cek apakah referensi ada
    if reference_id not in payments:
        return 'not_found', 0
    
    payment = payments[reference_id]
    status = payment.get('status', 'failed')
    amount = payment.get('amount', 0)
    
    # Simulasi perubahan status berdasarkan waktu dan kebetulan
    # Hanya lakukan ini jika status masih pending
    if status == 'pending':
        # Persentase kemungkinan pembayaran berhasil saat di-cek
        # Simulasi 30% kemungkinan pembayaran sudah selesai saat di-cek
        if random.random() < 0.3:
            payments[reference_id]['status'] = 'completed'
            payments[reference_id]['paid_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_payments(payments)
            return 'completed', amount
    
    return status, amount


def simulate_payment(reference_id):
    """
    Simulasi melakukan pembayaran (untuk testing).
    
    :param reference_id: ID Referensi pembayaran
    :return: True jika berhasil, False jika gagal
    """
    # Load data pembayaran
    payments = load_payments()
    
    # Cek apakah referensi ada
    if reference_id not in payments:
        return False
    
    payment = payments[reference_id]
    
    # Update status menjadi completed
    payments[reference_id]['status'] = 'completed'
    payments[reference_id]['paid_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Simpan perubahan
    save_payments(payments)
    
    return True


def get_pending_payments():
    """
    Mendapatkan semua pembayaran yang masih pending.
    Berguna untuk callback simulasi.
    
    :return: List pembayaran pending
    """
    payments = load_payments()
    pending = []
    
    for ref_id, payment in payments.items():
        if payment.get('status') == 'pending':
            pending.append(payment)
    
    return pending


def process_callbacks():
    """
    Simulasi callback dari payment gateway.
    Berguna untuk dijalankan secara berkala untuk memproses pembayaran pending.
    
    :return: List pembayaran yang diproses
    """
    payments = load_payments()
    processed = []
    
    for ref_id, payment in payments.items():
        if payment.get('status') == 'pending':
            # Simulasi 50% kemungkinan pembayaran selesai
            if random.random() < 0.5:
                payments[ref_id]['status'] = 'completed'
                payments[ref_id]['paid_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                processed.append(payment)
    
    # Simpan perubahan
    if processed:
        save_payments(payments)
    
    return processed


# Endpoint callback simulasi untuk webhook
# Dalam implementasi nyata, ini akan menjadi endpoint yang menerima callback dari payment gateway
def handle_payment_callback(callback_data):
    """
    Menangani callback dari payment gateway.
    
    :param callback_data: Data callback dari payment gateway
    :return: True jika berhasil, False jika gagal
    """
    reference_id = callback_data.get('reference_id')
    status = callback_data.get('status')
    
    if not reference_id or not status:
        return False
    
    # Load data pembayaran
    payments = load_payments()
    
    # Cek apakah referensi ada
    if reference_id not in payments:
        return False
    
    # Update status
    payments[reference_id]['status'] = status
    
    if status == 'completed':
        payments[reference_id]['paid_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Simpan perubahan
    save_payments(payments)
    
    return True
