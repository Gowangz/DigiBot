from tinydb import TinyDB, Query, where
from datetime import datetime
import json
import os

db_file = 'db.json'


class UsersDB:
    """Database untuk mengelola informasi pengguna."""

    def __init__(self):
        db = TinyDB(db_file)
        self.users = db.table('Users')
        self.User = Query()

    def register(self, user_id: int, username: str, first_name: str):
        """Mendaftarkan pengguna baru."""
        if self.get_by_id(user_id):
            raise Exception('Pengguna sudah terdaftar')
        
        self.users.insert({
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'balance': 0,
            'is_admin': False,
            'created_at': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    def get_by_id(self, user_id: int):
        """Mendapatkan data pengguna berdasarkan ID."""
        return self.users.get(self.User.user_id == user_id)
    
    def update_balance(self, user_id: int, amount: float):
        """Menambah atau mengurangi saldo pengguna."""
        user = self.get_by_id(user_id)
        if not user:
            raise Exception('Pengguna tidak ditemukan')
        
        current_balance = user.get('balance', 0)
        new_balance = current_balance + amount
        
        if new_balance < 0:
            raise Exception('Saldo tidak mencukupi')
        
        self.users.update({'balance': new_balance}, self.User.user_id == user_id)
        
        # Menambahkan transaksi ke dalam tabel Transactions
        TransactionsDB().add(user_id, amount, "topup" if amount > 0 else "purchase")
        
        return new_balance
    
    def get_all_users(self):
        """Mendapatkan semua pengguna."""
        return self.users.all()
    
    def make_admin(self, user_id: int):
        """Menjadikan pengguna sebagai admin."""
        self.users.update({'is_admin': True}, self.User.user_id == user_id)
    
    def update_last_login(self, user_id: int):
        """Memperbarui waktu login terakhir."""
        self.users.update(
            {'last_login': datetime.today().strftime('%Y-%m-%d %H:%M:%S')}, 
            self.User.user_id == user_id
        )


class TransactionsDB:
    """Database untuk mengelola transaksi."""

    def __init__(self):
        db = TinyDB(db_file)
        self.transactions = db.table('Transactions')
    
    def add(self, user_id: int, amount: float, type_: str, details: str = "", reference_id: str = ""):
        """
        Menambahkan transaksi baru.
        
        :param user_id: ID pengguna
        :param amount: Jumlah transaksi (positif untuk topup, negatif untuk purchase)
        :param type_: Jenis transaksi ('topup', 'purchase', 'refund', dll)
        :param details: Detail tambahan tentang transaksi
        :param reference_id: ID referensi eksternal (misalnya dari payment gateway)
        """
        self.transactions.insert({
            'user_id': user_id,
            'amount': amount,
            'type': type_,
            'details': details,
            'reference_id': reference_id,
            'timestamp': datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def get_by_user(self, user_id: int):
        """Mendapatkan semua transaksi untuk pengguna tertentu."""
        Transaction = Query()
        return self.transactions.search(Transaction.user_id == user_id)
    
    def get_by_reference(self, reference_id: str):
        """Mendapatkan transaksi berdasarkan ID referensi."""
        Transaction = Query()
        return self.transactions.get(Transaction.reference_id == reference_id)


class UserDropletsDB:
    """Database untuk mengelola droplet pengguna."""

    def __init__(self):
        db = TinyDB(db_file)
        self.user_droplets = db.table('UserDroplets')
        self.UserDroplet = Query()
    
    def add(self, user_id: int, doc_id: int, droplet_id: int):
        """Menambahkan droplet ke daftar droplet pengguna."""
        self.user_droplets.insert({
            'user_id': user_id,
            'account_doc_id': doc_id,
            'droplet_id': droplet_id,
            'created_at': datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def get_by_user(self, user_id: int):
        """Mendapatkan semua droplet untuk pengguna tertentu."""
        return self.user_droplets.search(self.UserDroplet.user_id == user_id)
    
    def get_droplet(self, user_id: int, droplet_id: int):
        """Mendapatkan detail droplet berdasarkan ID."""
        return self.user_droplets.get(
            (self.UserDroplet.user_id == user_id) & 
            (self.UserDroplet.droplet_id == droplet_id)
        )
    
    def remove(self, user_id: int, droplet_id: int):
        """Menghapus droplet dari daftar droplet pengguna."""
        self.user_droplets.remove(
            (self.UserDroplet.user_id == user_id) & 
            (self.UserDroplet.droplet_id == droplet_id)
        )
