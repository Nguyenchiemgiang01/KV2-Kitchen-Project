import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL         = os.getenv("DATABASE_URL", "sqlite:///./facedb.db")
MODEL_NAME           = os.getenv("MODEL_NAME", "buffalo_l")
MODEL_ROOT           = os.getenv("MODEL_ROOT", "./ai_models")
DET_SIZE             = (640, 640)
CTX_ID               = int(os.getenv("CTX_ID", -1))
SIMILARITY_THRESHOLD = float(os.getenv("THRESHOLD", 0.35))
DATASET_DIR          = os.getenv("DATASET_DIR", "./dataset")