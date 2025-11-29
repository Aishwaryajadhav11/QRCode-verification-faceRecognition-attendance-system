import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change")
    QR_SIGNING_SECRET = os.environ.get("QR_SIGNING_SECRET", "change-me")
    PUBLIC_BASE_URL = (os.environ.get("PUBLIC_BASE_URL", "http://localhost:5000") or "").strip() or "http://localhost:5000"
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
    IP_HASH_SALT = os.environ.get("IP_HASH_SALT", "ip-salt")
    # Force face verification to be required for now, regardless of environment variables.
    # If you want to toggle via .env later, change this back to reading REQUIRE_FACE from os.environ.
    REQUIRE_FACE = True
    FACE_DATA_DIR = os.environ.get("FACE_DATA_DIR", os.path.join(os.getcwd(), "data", "faces"))
    # Backend: 'fr' (face_recognition encodings), 'insightface', 'sface', or 'lbph' (legacy).
    FACE_BACKEND = os.environ.get("FACE_BACKEND", "fr").lower()
    # InsightFace similarity threshold (cosine similarity >= threshold passes)
    FACE_SIMILARITY_THRESHOLD = float(os.environ.get("FACE_SIMILARITY_THRESHOLD", "0.38"))
    # Legacy LBPH threshold (lower is better). Not used when FACE_BACKEND=insightface
    FACE_CONFIDENCE_THRESHOLD = float(os.environ.get("FACE_CONFIDENCE_THRESHOLD", "70"))
    # OpenCV SFace/YuNet model paths (used when FACE_BACKEND=sface)
    FACE_SFACE_DET_MODEL = os.environ.get(
        "FACE_SFACE_DET_MODEL",
        os.path.join(os.getcwd(), "data", "models", "face_detection_yunet_2023mar.onnx"),
    )
    FACE_SFACE_REC_MODEL = os.environ.get(
        "FACE_SFACE_REC_MODEL",
        os.path.join(os.getcwd(), "data", "models", "face_recognition_sface_2021dec.onnx"),
    )
    FACE_ENCODING_TOLERANCE = float(os.environ.get("FACE_ENCODING_TOLERANCE", "0.6"))
    FACE_TOKEN_TTL = int(os.environ.get("FACE_TOKEN_TTL", "120"))
    FACE_SIGNING_SECRET = os.environ.get("FACE_SIGNING_SECRET", SECRET_KEY)
    # Geofence radius in meters for attendance acceptance
    GEOFENCE_METERS = float(os.environ.get("GEOFENCE_METERS", "50"))

def load_config():
    return Config()
