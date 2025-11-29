import os
import urllib.request
from typing import Dict, List, Tuple

import cv2
import numpy as np

_YUNET_CANDIDATES = [
    # Stable raw links
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2022mar.onnx",
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    # Fallback GitHub raw path
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2022mar.onnx",
]
_SFACE_CANDIDATES = [
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
]


class SFaceService:
    def __init__(self, data_dir: str, det_model_path: str, rec_model_path: str, similarity_threshold: float = 0.38):
        self.data_dir = data_dir
        self.det_model_path = det_model_path
        self.rec_model_path = rec_model_path
        self.similarity_threshold = similarity_threshold
        self._det = None
        self._rec = None
        self._index: Dict[str, List[np.ndarray]] = {}
        self._indexed = False
        self._ready = False
        try:
            self._ensure_models()
            # Initialize models (compat across OpenCV versions)
            det_cls = getattr(cv2, "FaceDetectorYN", None)
            if det_cls is not None and hasattr(det_cls, "create"):
                self._det = det_cls.create(self.det_model_path, "", (320, 320), 0.6, 0.3, 5000)
            elif hasattr(cv2, "FaceDetectorYN_create"):
                self._det = cv2.FaceDetectorYN_create(self.det_model_path, "", (320, 320), 0.6, 0.3, 5000)

            rec_cls = getattr(cv2, "FaceRecognizerSF", None)
            if rec_cls is not None and hasattr(rec_cls, "create"):
                self._rec = rec_cls.create(self.rec_model_path, "")
            elif hasattr(cv2, "FaceRecognizerSF_create"):
                self._rec = cv2.FaceRecognizerSF_create(self.rec_model_path, "")

            self._ready = bool(self._det is not None and self._rec is not None)
        except Exception:
            # Leave _ready False; verification will return model_not_ready
            self._det = None
            self._rec = None

    def _ensure_models(self) -> None:
        os.makedirs(os.path.dirname(self.det_model_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.rec_model_path), exist_ok=True)
        if not os.path.isfile(self.det_model_path):
            if not self._download_any(_YUNET_CANDIDATES, self.det_model_path):
                raise RuntimeError(
                    f"Failed to download YuNet model. Please download manually to {self.det_model_path}\n"
                    "Links:\n"
                    "- https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2022mar.onnx\n"
                    "- https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx\n"
                )
        if not os.path.isfile(self.rec_model_path):
            if not self._download_any(_SFACE_CANDIDATES, self.rec_model_path):
                raise RuntimeError(
                    f"Failed to download SFace model. Please download manually to {self.rec_model_path}\n"
                    "Link:\n"
                    "- https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx\n"
                )

    def _download_any(self, urls: List[str], dst: str) -> bool:
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r, open(dst, "wb") as f:
                    f.write(r.read())
                return True
            except Exception:
                continue
        return False

    def _detect_faces(self, bgr: np.ndarray) -> np.ndarray:
        if self._det is None:
            return np.empty((0, 15), dtype=np.float32)
        try:
            h, w = bgr.shape[:2]
            self._det.setInputSize((w, h))
            _, faces = self._det.detect(bgr)
        except Exception:
            faces = None
        if faces is None:
            return np.empty((0, 15), dtype=np.float32)
        return faces

    def _embed(self, bgr: np.ndarray) -> np.ndarray | None:
        if self._rec is None:
            return None
        faces = self._detect_faces(bgr)
        work_img = bgr
        if faces.shape[0] == 0:
            # Try with an upscaled image to help detection on small faces
            h, w = bgr.shape[:2]
            scale = 1.0
            # Aim for ~640 max dimension
            max_dim = max(h, w)
            if max_dim < 640:
                scale = min(2.0, 640.0 / float(max_dim))
            if scale > 1.0:
                new_w = int(round(w * scale))
                new_h = int(round(h * scale))
                work_img = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                faces = self._detect_faces(work_img)
            if faces.shape[0] == 0:
                return None
        # Choose largest face by area
        areas = (faces[:, 2] * faces[:, 3])
        idx = int(np.argmax(areas))
        face = faces[idx]
        try:
            aligned = self._rec.alignCrop(work_img, face)
            feat = self._rec.feature(aligned)
        except Exception:
            return None
        # Normalize to unit vector for cosine sim
        norm = np.linalg.norm(feat) + 1e-9
        return (feat / norm).astype(np.float32)

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        # Flatten arrays to handle 2D embeddings from OpenCV
        a_flat = a.flatten()
        b_flat = b.flatten()
        return float(np.dot(a_flat, b_flat))

    def ensure_indexed(self) -> bool:
        if not self._ready:
            return False
        if self._indexed and self._index:
            return True
        self._index.clear()
        if not os.path.isdir(self.data_dir):
            return False
        for roll_no in sorted(os.listdir(self.data_dir)):
            roll_path = os.path.join(self.data_dir, roll_no)
            if not os.path.isdir(roll_path):
                continue
            embs: List[np.ndarray] = []
            for fname in os.listdir(roll_path):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                img = cv2.imread(os.path.join(roll_path, fname))
                if img is None:
                    continue
                emb = self._embed(img)
                if emb is not None:
                    embs.append(emb)
            if embs:
                self._index[roll_no] = embs
        self._indexed = True
        return bool(self._index)

    def verify(self, roll_no: str, image_bytes: bytes) -> Tuple[bool, float, str]:
        if not self._ready:
            return False, 0.0, "model_not_ready"
        if not self.ensure_indexed():
            return False, 0.0, "index_empty"
        if roll_no not in self._index:
            return False, 0.0, "unknown_roll"
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, "invalid_image"
        probe = self._embed(img)
        if probe is None:
            return False, 0.0, "no_face_detected"
        best = 0.0
        for ref in self._index[roll_no]:
            sim = self._cosine(probe, ref)
            if sim > best:
                best = sim
        if best >= float(self.similarity_threshold):
            return True, best, "ok"
        return False, best, "low_similarity"

    def reload(self) -> bool:
        self._index.clear()
        self._indexed = False
        return self.ensure_indexed()

    def enrolled_rolls(self) -> List[str]:
        if not self.ensure_indexed():
            return []
        return sorted(self._index.keys())

    def status(self) -> Dict[str, object]:
        return {
            "ready": bool(self._ready and self._det is not None and self._rec is not None),
            "indexCount": len(self._index) if self._index else 0,
            "dataDir": self.data_dir,
        }
