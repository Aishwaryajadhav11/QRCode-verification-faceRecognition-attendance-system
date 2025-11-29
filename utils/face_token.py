import base64
import hashlib
import hmac
import time
from typing import Tuple


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64u_dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_face_token(roll_no: str, lecture_id: str, confidence: float, secret: str) -> str:
    ts = int(time.time())
    payload = f"{roll_no}|{lecture_id}|{ts}|{confidence:.4f}".encode()
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return _b64u(payload + b"." + sig)


def verify_face_token(token: str, roll_no: str, lecture_id: str, secret: str, ttl_seconds: int) -> Tuple[bool, float]:
    try:
        raw = _b64u_dec(token)
        payload, sig = raw.split(b".", 1)
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected_sig):
            return False, 0.0
        parts = payload.decode().split("|")
        if len(parts) != 4:
            return False, 0.0
        p_roll, p_lid, p_ts, p_conf = parts
        if p_roll != roll_no or p_lid != lecture_id:
            return False, 0.0
        ts = int(p_ts)
        if int(time.time()) - ts > int(ttl_seconds):
            return False, 0.0
        return True, float(p_conf)
    except Exception:
        return False, 0.0
