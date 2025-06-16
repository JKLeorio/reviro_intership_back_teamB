import secrets
import string

alphabet = string.ascii_letters + string.digits

PASSWORD_LENGTH = 15

def generate_password() -> str:
    """
    Generate and return a password of length specified in PASSWORD_LENGTH
    """
    password = ''.join(secrets.choice(alphabet) for i in range(PASSWORD_LENGTH))
    return password