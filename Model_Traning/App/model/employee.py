import datetime
import pickle
import numpy as np
from sqlalchemy import Column, String, LargeBinary, DateTime
from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    emp_id     = Column(String(50),  primary_key=True, index=True)
    name       = Column(String(200), nullable=False)
    embedding  = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    def set_embedding(self, vector: np.ndarray):
        self.embedding = pickle.dumps(vector.astype(np.float32))

    def get_embedding(self) -> np.ndarray:
        return pickle.loads(self.embedding)