import io
import os
from typing import Dict, List, Tuple

import face_recognition
import numpy as np


class FaceEncodingService:
    def __init__(self, data_dir: str, tolerance: float = 0.6):
        self.data_dir = data_dir
        self.tolerance = tolerance
        self._index: Dict[str, List[np.ndarray]] = {}
        self._indexed = False

    def _encode_image(self, image_array: np.ndarray) -> np.ndarray | None:
        encodings = face_recognition.face_encodings(image_array)
        if not encodings:
            return None
        return encodings[0].astype(np.float32)

    def _encode_file(self, path: str) -> np.ndarray | None:
        try:
            image = face_recognition.load_image_file(path)
        except Exception:
            return None
        return self._encode_image(image)

    def ensure_indexed(self) -> bool:
        if self._indexed and self._index:
            return True
        self._index.clear()
        if not os.path.isdir(self.data_dir):
            return False
        for roll_no in sorted(os.listdir(self.data_dir)):
            roll_path = os.path.join(self.data_dir, roll_no)
            if not os.path.isdir(roll_path):
                continue
            encs: List[np.ndarray] = []
            for fname in os.listdir(roll_path):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                enc = self._encode_file(os.path.join(roll_path, fname))
                if enc is not None:
                    encs.append(enc)
            if encs:
                self._index[roll_no] = encs
        self._indexed = True
        return bool(self._index)

    def verify(self, roll_no: str, image_bytes: bytes) -> Tuple[bool, float, str]:
        if not self.ensure_indexed():
            return False, 1.0, "index_empty"
        if roll_no not in self._index:
            return False, 1.0, "unknown_roll"
        try:
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
        except Exception:
            return False, 1.0, "invalid_image"
        encoding = self._encode_image(image)
        if encoding is None:
            return False, 1.0, "no_face_detected"
        best_distance = 1.0
        for ref in self._index[roll_no]:
            dist = float(np.linalg.norm(ref - encoding))
            if dist < best_distance:
                best_distance = dist
        if best_distance <= float(self.tolerance):
            return True, best_distance, "ok"
        return False, best_distance, "low_similarity"

    def reload(self) -> bool:
        self._index.clear()
        self._indexed = False
        return self.ensure_indexed()

    def enrolled_rolls(self) -> List[str]:
        if not self.ensure_indexed():
            return []
        return sorted(self._index.keys())

    def status(self) -> Dict[str, object]:
        ready = self.ensure_indexed()
        return {
            "ready": ready,
            "indexCount": len(self._index),
            "dataDir": self.data_dir,
            "tolerance": self.tolerance,
        }

