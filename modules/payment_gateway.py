import time
import json
import requests
import logging
import random
import qrcode
from io import BytesIO
from os import path, environ
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='payment_gateway.log'
)
logger = logging.getLogger('payment_gateway')

# Load config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    PAYMENT_CONFIG = config['BOT']['PAYMENT_CONFIG']
    MERCHANT_ID = PAYMENT_CONFIG.get('MERCHANT_ID')
    API_KEY = PAYMENT_CONFIG.get('API_KEY')
    DATA_QRIS = PAYMENT_CONFIG.get('DATA_QRIS')
    CALLBACK_URL = PAYMENT_CONFIG.get('CALLBACK_URL')
    CHECK_INTERVAL = int(PAYMENT_CONFIG.get('CHECK_INTERVAL', 5))
    EXPIRE_TIME = int(PAYMENT_CONFIG.get('EXPIRE_TIME', 30))
    
    # Validate required config
    if not all([MERCHANT_ID, API_KEY, DATA_QRIS, CALLBACK_URL]):
        raise ValueError("Missing required payment configuration")
        
except Exception as e:
    logger.error(f"Failed to load config: {str(e)}")
    raise RuntimeError(f"Payment gateway initialization failed: {str(e)}")

# Global state
processed_transactions = {}
pending_deposits = {}
payment_callbacks = {}

def register_payment_callback(reference_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
    """Register callback untuk notifikasi pembayaran."""
    try:
        payment_callbacks[reference_id] = callback
        logger.info(f"Registered payment callback for {reference_id}")
    except Exception as e:
        logger.error(f"Failed to register payment callback for {reference_id}: {str(e)}")
        raise

def notify_payment_success(reference_id: str, payment_data: Dict[str, Any]) -> None:
    """Notifikasi pembayaran berhasil ke callback yang terdaftar."""
    try:
        callback = payment_callbacks.get(reference_id)
        if callback:
            callback(payment_data)
            logger.info(f"Payment success notification sent for {reference_id}")
            del payment_callbacks[reference_id]
        else:
            logger.warning(f"No callback found for payment {reference_id}")
    except Exception as e:
        logger.error(f"Error in payment callback for {reference_id}: {str(e)}")
        raise

def generate_qris(amount: int) -> BytesIO:
    """Generate QRIS code with amount."""
    try:
        if amount < 1000:
            raise ValueError("Minimum amount is Rp 1.000")
            
        response = requests.get(
            "http://orkut.cekid.games/qris/generate",
            params={
                "nominal": amount,
                "qris": DATA_QRIS
            },
            headers={
                'Accept': 'image/png',
                'Origin': 'http://orkut.cekid.games',
                'Referer': 'http://orkut.cekid.games',
                'User-Agent': 'Mozilla/5.0',
                'Connection': 'keep-alive'
            },
            timeout=30
        )
        
        response.raise_for_status()
        
        if not response.content:
            raise ValueError("Empty response from QRIS generator")
            
        return BytesIO(response.content)
            
    except requests.RequestException as e:
        logger.error(f"Network error generating QRIS: {str(e)}")
        raise ValueError("Failed to connect to QRIS service")
    except Exception as e:
        logger.error(f"Error generating QRIS: {str(e)}")
        raise

def check_payment_status(reference_id: str) -> Dict[str, Any]:
    """Check payment status with improved verification."""
    try:
        deposit = pending_deposits.get(reference_id)
        if not deposit:
            logger.warning(f"Payment {reference_id} not found in pending deposits")
            return {'status': 'not_found', 'amount': 0}

        # Check if expired
        if (datetime.now().timestamp() - deposit['timestamp']) > (EXPIRE_TIME * 60):
            logger.info(f"Payment {reference_id} has expired")
            if reference_id in pending_deposits:
                del pending_deposits[reference_id]
            return {'status': 'expired', 'amount': deposit['original_amount']}

        response = requests.get(
            f"{CALLBACK_URL}/{MERCHANT_ID}/{API_KEY}",
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Payment check response for {reference_id}: {data}")
        
        if isinstance(data.get('data'), list):
            transactions = data['data']
            for tx in transactions:
                tx_amount = int(tx.get('amount', 0))
                
                if tx_amount == deposit['amount']:
                    # Payment found
                    payment_data = {
                        'status': 'completed',
                        'amount': deposit['original_amount'],
                        'payment_details': {
                            'bank': tx.get('brand_name', 'QRIS'),
                            'ref': tx.get('issuer_reff', 'N/A'),
                            'buyer': tx.get('buyer_reff', '').split('/')[1].strip() if tx.get('buyer_reff') else 'QRIS Payment'
                        }
                    }
                    
                    # Notify callback
                    notify_payment_success(reference_id, payment_data)
                    
                    # Remove from pending
                    if reference_id in pending_deposits:
                        del pending_deposits[reference_id]
                    
                    logger.info(f"Payment {reference_id} completed successfully")
                    return payment_data

        return {'status': 'pending', 'amount': deposit['original_amount']}

    except requests.RequestException as e:
        logger.error(f"Network error checking payment {reference_id}: {str(e)}")
        return {'status': 'error', 'amount': deposit['original_amount']}
    except Exception as e:
        logger.error(f"Error checking payment {reference_id}: {str(e)}")
        return {'status': 'error', 'amount': deposit['original_amount']}

def create_payment(user_id: int, amount: int) -> Tuple[Dict[str, Any], str]:
    """Create new payment with unique amount."""
    try:
        # Validate minimum amount
        if amount < 1000:
            return None, "Minimal top up Rp 1.000"

        # Generate unique amount
        final_amount = amount + random.randint(1, 99)
        
        # Generate reference ID
        reference_id = f"TX-{int(time.time())}-{user_id}"
        
        # Generate QR code
        qr_buffer = generate_qris(final_amount)
        if not qr_buffer:
            return None, "Gagal membuat QR code"
        
        # Save pending deposit
        pending_deposits[reference_id] = {
            'user_id': user_id,
            'amount': final_amount,
            'original_amount': amount,
            'timestamp': datetime.now().timestamp(),
            'status': 'pending'
        }
        
        logger.info(f"Created payment {reference_id} for user {user_id}: {final_amount}")
        
        return {
            'qr_buffer': qr_buffer,
            'amount': final_amount,
            'reference_id': reference_id,
            'expire_time': EXPIRE_TIME
        }, None

    except ValueError as e:
        logger.warning(f"Validation error creating payment for user {user_id}: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error creating payment for user {user_id}: {str(e)}")
        return None, "Terjadi kesalahan sistem"

def cleanup_expired_payments():
    """Cleanup expired payments and callbacks."""
    try:
        current_time = datetime.now().timestamp()
        
        # Cleanup expired pending deposits
        expired_refs = []
        for ref_id, deposit in pending_deposits.items():
            if current_time - deposit['timestamp'] > (EXPIRE_TIME * 60):
                expired_refs.append(ref_id)
        
        for ref_id in expired_refs:
            if ref_id in pending_deposits:
                del pending_deposits[ref_id]
            if ref_id in payment_callbacks:
                del payment_callbacks[ref_id]
            logger.info(f"Removed expired payment: {ref_id}")
            
    except Exception as e:
        logger.error(f"Error cleaning up expired payments: {str(e)}")

def start_cleanup_scheduler():
    """Start cleanup and payment check scheduler."""
    import threading
    
    def cleanup_task():
        while True:
            try:
                cleanup_expired_payments()
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
            finally:
                time.sleep(300)  # 5 minutes
            
    def check_payments_task():
        while True:
            try:
                # Check all pending payments
                for ref_id in list(pending_deposits.keys()):
                    logger.info(f"Checking payment {ref_id}")
                    result = check_payment_status(ref_id)
                    logger.info(f"Payment status for {ref_id}: {result}")
            except Exception as e:
                logger.error(f"Error in payment check cycle: {str(e)}")
            finally:
                time.sleep(CHECK_INTERVAL)
            
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_task, name="payment_cleanup")
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # Start payment check thread
    check_thread = threading.Thread(target=check_payments_task, name="payment_check")
    check_thread.daemon = True
    check_thread.start()
    
    logger.info("Payment gateway scheduler started")

# Start scheduler
try:
    start_cleanup_scheduler()
except Exception as e:
    logger.error(f"Failed to start payment gateway scheduler: {str(e)}")
    raise RuntimeError("Payment gateway initialization failed")
