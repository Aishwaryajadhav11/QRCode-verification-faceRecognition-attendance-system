import os
from typing import Dict, List, Tuple

import cv2
import numpy as np
from insightface.app import FaceAnalysis


class InsightFaceService:
    def __init__(self, data_dir: str, similarity_threshold: float = 0.38):
        self.data_dir = data_dir
        self.similarity_threshold = similarity_threshold
        # Initialize app with CPU provider
        self._app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        # det_size impacts detection performance; 640x640 is a good default
        self._app.prepare(ctx_id=0, det_size=(640, 640))
        # Index of embeddings per roll number
        self._index: Dict[str, List[np.ndarray]] = {}
        self._indexed = False

    def _embed_face(self, bgr_img: np.ndarray) -> np.ndarray | None:
        # InsightFace expects BGR
        faces = self._app.get(bgr_img)
        if not faces:
            return None
        # choose largest face
        faces.sort(key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)
        emb = getattr(faces[0], 'normed_embedding', None)
        if emb is None:
            # Some models use 'embedding', normalize
            raw = getattr(faces[0], 'embedding', None)
            if raw is None:
                return None
            v = np.array(raw, dtype=np.float32)
            n = np.linalg.norm(v) + 1e-9
            emb = (v / n).astype(np.float32)
        return np.asarray(emb, dtype=np.float32)

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))

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
            embs: List[np.ndarray] = []
            for fname in os.listdir(roll_path):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                img_path = os.path.join(roll_path, fname)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                emb = self._embed_face(img)
                if emb is not None:
                    embs.append(emb)
            if embs:
                self._index[roll_no] = embs
        self._indexed = True
        return bool(self._index)

    def verify(self, roll_no: str, image_bytes: bytes) -> Tuple[bool, float, str]:
        if not self.ensure_indexed():
            return False, 0.0, 'index_empty'
        if roll_no not in self._index:
            return False, 0.0, 'unknown_roll'
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, 'invalid_image'
        probe = self._embed_face(img)
        if probe is None:
            return False, 0.0, 'no_face_detected'
        best = 0.0
        for ref in self._index[roll_no]:
            sim = self._cosine(probe, ref)
            if sim > best:
                best = sim
        if best >= float(self.similarity_threshold):
            return True, best, 'ok'
        return False, best, 'low_similarity'

    def reload(self) -> bool:
        self._index.clear()
        self._indexed = False
        return self.ensure_indexed()
