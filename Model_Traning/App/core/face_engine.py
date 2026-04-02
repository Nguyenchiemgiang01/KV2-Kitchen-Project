import insightface
import numpy as np
import cv2
from config import MODEL_NAME, MODEL_ROOT, DET_SIZE, CTX_ID


class FaceEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        print(f"Đang load model {MODEL_NAME}...")
        self.model = insightface.app.FaceAnalysis(
            name=MODEL_NAME,
            root=MODEL_ROOT,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.model.prepare(ctx_id=CTX_ID, det_size=DET_SIZE)
        self._initialized = True
        print("Load model thành công.")

    def get_embedding(self, image: np.ndarray):
        faces = self.model.get(image)
        if not faces:
            return None
        face = max(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
        )
        return face.embedding

    def get_embedding_from_path(self, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            print(f"  Không đọc được file: {image_path}")
            return None
        return self.get_embedding(img)

    def get_embedding_from_bytes(self, image_bytes: bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return self.get_embedding(img)


face_engine = FaceEngine()