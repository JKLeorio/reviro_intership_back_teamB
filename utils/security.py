import secrets
import bcrypt


def generate_otp6() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_code(code: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(code.encode('utf-8'), salt=salt)
    return hashed.decode("utf-8")

def verify_code_hash(code: str, code_hash: str) -> bool:
    try:
        return bcrypt.checkpw(code.encode("utf-8"), code_hash.encode("utf-8"))
    except ValueError:
        return False

