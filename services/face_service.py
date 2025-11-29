import os
from typing import Dict, List, Tuple

import cv2
import numpy as np


class FaceService:
    def __init__(self, data_dir: str, confidence_threshold: float = 70.0):
        self.data_dir = data_dir
        self.confidence_threshold = confidence_threshold
        self._recognizer = None
        self._label_to_roll: Dict[int, str] = {}
        self._roll_to_label: Dict[str, int] = {}
        self._cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
        self._trained = False

    def _prepare_dataset(self) -> Tuple[List[np.ndarray], List[int]]:
        faces: List[np.ndarray] = []
        labels: List[int] = []
        if not os.path.isdir(self.data_dir):
            return faces, labels
        label_id = 0
        for roll_no in sorted(os.listdir(self.data_dir)):
            roll_path = os.path.join(self.data_dir, roll_no)
            if not os.path.isdir(roll_path):
                continue
            if roll_no not in self._roll_to_label:
                self._roll_to_label[roll_no] = label_id
                self._label_to_roll[label_id] = roll_no
                label_id += 1
            lid = self._roll_to_label[roll_no]
            for fname in os.listdir(roll_path):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                img_path = os.path.join(roll_path, fname)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                face = self._extract_face(gray)
                if face is None:
                    # Fallback: use entire image resized
                    face = cv2.resize(gray, (200, 200))
                faces.append(face)
                labels.append(lid)
        return faces, labels

    def _extract_face(self, gray_img: np.ndarray) -> np.ndarray | None:
        rects = self._cascade.detectMultiScale(gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        if len(rects) == 0:
            return None
        # choose largest
        x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
        crop = gray_img[y : y + h, x : x + w]
        return cv2.resize(crop, (200, 200))

    def ensure_trained(self) -> bool:
        if self._trained and self._recognizer is not None:
            return True
        faces, labels = self._prepare_dataset()
        if not faces:
            return False
        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._recognizer.train(faces, np.array(labels))
        self._trained = True
        return True

    def verify(self, roll_no: str, image_bytes: bytes) -> Tuple[bool, float, str]:
        """Return (ok, confidence, reason). For LBPH, lower confidence is better."""
        if not self.ensure_trained():
            return False, 1e9, "model_not_trained"
        if roll_no not in self._roll_to_label:
            return False, 1e9, "unknown_roll"
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 1e9, "invalid_image"
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face = self._extract_face(gray)
        if face is None:
            return False, 1e9, "no_face_detected"
        label_id, conf = self._recognizer.predict(face)
        expected_id = self._roll_to_label[roll_no]
        if label_id == expected_id and conf <= float(self.confidence_threshold):
            return True, float(conf), "ok"
        return False, float(conf), "mismatch_or_low_confidence"

    def reload(self) -> bool:
        self._recognizer = None
        self._label_to_roll.clear()
        self._roll_to_label.clear()
        self._trained = False
        return self.ensure_trained()
