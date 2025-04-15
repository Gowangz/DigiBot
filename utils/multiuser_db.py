import json
from typing import Dict, Any, Optional, List
from tinydb import TinyDB, Query
from datetime import datetime

class UsersDB:
    def __init__(self):
        self.db = TinyDB('users.json')
        self.User = Query()

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self.db.get(self.User.id == user_id)
        
    def register(self, user_id: int, username: str, first_name: str) -> None:
        """Register a new user."""
        # Check if user already exists
        if self.get_by_id(user_id):
            raise Exception("User already registered")
            
        # Create new user data
        user_data = {
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'balance': 0,
            'transactions': [],
            'created_at': datetime.now().timestamp()
        }
        
        # Insert new user
        self.db.insert(user_data)

    def get_balance(self, user_id: int) -> int:
        """Get user balance."""
        user = self.get_by_id(user_id)
        if not user:
            raise Exception("User not found")
        return user.get('balance', 0)

    def update_balance(self, user_id: int, amount: int) -> int:
        """Update user balance and return new balance."""
        user = self.get_by_id(user_id)
        if not user:
            raise Exception("User not found")
        
        current_balance = user.get('balance', 0)
        new_balance = current_balance + amount
        
        if new_balance < 0:
            raise Exception("Insufficient balance")
        
        self.db.update({'balance': new_balance}, self.User.id == user_id)
        return new_balance

    def update_user(self, user_id: int, data: Dict[str, Any]) -> None:
        """Update user data."""
        user = self.get_by_id(user_id)
        if not user:
            raise Exception("User not found")
        
        # Merge existing data with new data
        updated_data = {**user, **data}
        self.db.update(updated_data, self.User.id == user_id)

    def add_transaction(self, user_id: int, transaction: Dict[str, Any]) -> None:
        """Add transaction to user history."""
        user = self.get_by_id(user_id)
        if not user:
            raise Exception("User not found")
        
        # Validate transaction data
        required_fields = ['type', 'amount', 'status']
        for field in required_fields:
            if field not in transaction:
                raise Exception(f"Missing required transaction field: {field}")
        
        # Get existing transactions or create empty list
        transactions = user.get('transactions', [])
        
        # Add new transaction
        transactions.append({
            **transaction,
            'timestamp': datetime.now().timestamp()
        })
        
        # Update user with new transactions
        self.update_user(user_id, {'transactions': transactions})

    def get_transactions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user transactions with limit."""
        user = self.get_by_id(user_id)
        if not user:
            raise Exception("User not found")
        
        transactions = user.get('transactions', [])
        
        # Sort by timestamp (newest first) and limit
        return sorted(
            transactions,
            key=lambda x: x.get('timestamp', 0),
            reverse=True
        )[:limit]

class TransactionsDB:
    def __init__(self):
        self.db = TinyDB('transactions.json')
        self.Transaction = Query()
        
    def add(self, user_id: int, amount: int, type_: str, details: str = None) -> None:
        """Add a new transaction."""
        transaction = {
            'user_id': user_id,
            'amount': amount,
            'type': type_,
            'details': details,
            'timestamp': datetime.now().timestamp()
        }
        self.db.insert(transaction)
        
    def get_by_user(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get transactions for a specific user."""
        transactions = self.db.search(self.Transaction.user_id == user_id)
        return sorted(
            transactions,
            key=lambda x: x.get('timestamp', 0),
            reverse=True
        )[:limit]

class UserDropletsDB:
    def __init__(self):
        self.db = TinyDB('user_droplets.json')
        self.UserDroplet = Query()
        
    def add(self, user_id: int, doc_id: int, droplet_id: int) -> None:
        """Add a new droplet association."""
        data = {
            'user_id': user_id,
            'doc_id': doc_id,
            'droplet_id': droplet_id,
            'created_at': datetime.now().timestamp()
        }
        self.db.insert(data)
        
    def get_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all droplets for a specific user."""
        return self.db.search(self.UserDroplet.user_id == user_id)
