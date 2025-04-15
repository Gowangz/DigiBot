from utils.multiuser_db import UsersDB

def check_auth(user_id: int) -> bool:
    """
    Memeriksa apakah pengguna sudah terdaftar.
    
    :param user_id: ID pengguna Telegram
    :return: True jika terdaftar, False jika belum
    """
    return bool(UsersDB().get_by_id(user_id))

def is_admin(user_id: int) -> bool:
    """
    Memeriksa apakah pengguna adalah admin.
    
    :param user_id: ID pengguna Telegram
    :return: True jika admin, False jika bukan
    """
    user = UsersDB().get_by_id(user_id)
    return bool(user and user.get('is_admin', False))
