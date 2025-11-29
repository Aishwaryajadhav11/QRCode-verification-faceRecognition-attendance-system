import base64
import hashlib
import hmac
import urllib.parse
from io import BytesIO

import qrcode

def sign_token(lecture_id: str, nonce: str, issued_at: int, secret: str) -> str:
    payload = f"{lecture_id}|{nonce}|{issued_at}".encode()
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(payload + b"." + sig).decode().rstrip("=")
    return token

def verify_token(token: str, lecture_id: str, nonce: str, issued_at: int, secret: str) -> bool:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode())
        parts = raw.split(b".", 1)
        if len(parts) != 2:
            return False
        payload, sig = parts
        expected_payload = f"{lecture_id}|{nonce}|{issued_at}".encode()
        if payload != expected_payload:
            return False
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False

def build_scan_url(public_base_url: str, lecture_id: str, token: str) -> str:
    base = public_base_url.rstrip("/")
    q = urllib.parse.urlencode({"lid": lecture_id, "t": token})
    return f"{base}/scan?{q}"

def generate_qr_png_bytes(data: str) -> bytes:
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
