"""Password hashing (bcrypt) and JWT handling."""

import datetime

import bcrypt
import jwt


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_token(user_id, secret, expiry_hours=24):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + datetime.timedelta(hours=expiry_hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token, secret):
    return jwt.decode(token, secret, algorithms=["HS256"])
