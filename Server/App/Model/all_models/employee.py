"""
============================================================
  models/employee.py
  Model: Employee — Nhân viên và embedding khuôn mặt
============================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Enum, Numeric, JSON, LargeBinary, DateTime
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship, Session

from .base import Base


class Employee(Base):
    """Danh sách nhân viên và embedding khuôn mặt."""

    __tablename__ = "employees"
    __table_args__ = {
        "mysql_engine":  "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
        "comment":       "Danh sách nhân viên và embedding khuôn mặt",
    }

    # ----------------------------------------------------------
    # COLUMNS
    # ----------------------------------------------------------

    emp_id      = Column(String(50),                primary_key=True,                            comment="Mã nhân viên — khóa chính")
    name        = Column(String(200),               nullable=False,                              comment="Họ và tên nhân viên")
    age         = Column(TINYINT(),                 nullable=True,                               comment="Tuổi nhân viên")
    gender      = Column(Enum("Nam", "Nữ", "Khác"), nullable=True,                              comment="Giới tính")
    height      = Column(Numeric(5, 2),             nullable=True,                               comment="Chiều cao (cm) — ví dụ: 170.50")
    weight      = Column(Numeric(5, 2),             nullable=True,                               comment="Cân nặng (kg) — ví dụ: 65.00")
    avatar_path = Column(JSON,                      nullable=True,                               comment='Danh sách đường dẫn ảnh — ["dataset/NV001/01.jpg"]')
    embedding   = Column(LargeBinary,               nullable=True,                               comment="Embedding vector 512-D (numpy array serialized)")
    is_deleted  = Column(TINYINT(1),                nullable=False, default=0,                   comment="Soft delete: 0 = đang hoạt động, 1 = đã xóa")
    created_at  = Column(DateTime,                  default=datetime.now,                        comment="Thời điểm đăng ký lần đầu")
    updated_at  = Column(DateTime,                  default=datetime.now, onupdate=datetime.now, comment="Thời điểm cập nhật gần nhất")

    # ----------------------------------------------------------
    # RELATIONSHIPS
    # ----------------------------------------------------------

    user            = relationship("User",          back_populates="employee", uselist=False)
    meal_list       = relationship("MealList",      back_populates="employee")
    attendance_logs = relationship("AttendanceLog", back_populates="employee")

    # ==========================================================
    # SELECT
    # ==========================================================

    @classmethod
    def get_by_id(cls, db: Session, emp_id: str) -> Optional["Employee"]:
        """
        Lấy nhân viên theo emp_id (kể cả đã xóa mềm).

        Ví dụ:
            emp = Employee.get_by_id(db, "NV001")
        """
        return db.get(cls, emp_id)

    @classmethod
    def get_active_by_id(cls, db: Session, emp_id: str) -> Optional["Employee"]:
        """
        Lấy nhân viên đang hoạt động theo emp_id.

        Ví dụ:
            emp = Employee.get_active_by_id(db, "NV001")
        """
        return (
            db.query(cls)
            .filter(cls.emp_id == emp_id, cls.is_deleted == 0)
            .first()
        )

    @classmethod
    def get_all(cls, db: Session) -> list["Employee"]:
        """
        Lấy tất cả nhân viên đang hoạt động.

        Ví dụ:
            employees = Employee.get_all(db)
        """
        return db.query(cls).filter(cls.is_deleted == 0).all()

    @classmethod
    def get_by_name(cls, db: Session, keyword: str) -> list["Employee"]:
        """
        Tìm kiếm nhân viên theo tên (không phân biệt hoa thường).

        Ví dụ:
            results = Employee.get_by_name(db, "nguyễn")
        """
        return (
            db.query(cls)
            .filter(cls.name.ilike(f"%{keyword}%"), cls.is_deleted == 0)
            .all()
        )

    @classmethod
    def get_by_gender(cls, db: Session, gender: str) -> list["Employee"]:
        """
        Lấy danh sách nhân viên theo giới tính.

        Ví dụ:
            employees = Employee.get_by_gender(db, "Nam")
        """
        return (
            db.query(cls)
            .filter(cls.gender == gender, cls.is_deleted == 0)
            .all()
        )

    # ==========================================================
    # CREATE
    # ==========================================================

    @classmethod
    def create(cls, db: Session, **kwargs) -> "Employee":
        """
        Tạo nhân viên mới.

        Ví dụ:
            emp = Employee.create(
                db,
                emp_id = "NV001",
                name   = "Nguyễn Văn An",
                age    = 28,
                gender = "Nam",
            )
        """
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def bulk_create(cls, db: Session, records: list[dict]) -> list["Employee"]:
        """
        Tạo nhiều nhân viên cùng lúc.

        Ví dụ:
            Employee.bulk_create(db, [
                {"emp_id": "NV001", "name": "Nguyễn Văn An"},
                {"emp_id": "NV002", "name": "Trần Thị Bình"},
            ])
        """
        instances = [cls(**r) for r in records]
        db.add_all(instances)
        db.commit()
        return instances

    # ==========================================================
    # UPDATE
    # ==========================================================

    @classmethod
    def update(cls, db: Session, emp_id: str, **kwargs) -> Optional["Employee"]:
        """
        Cập nhật thông tin nhân viên theo emp_id.
        Trả về None nếu không tìm thấy.

        Ví dụ:
            emp = Employee.update(db, "NV001", name="Tên Mới", age=30)
        """
        instance = cls.get_active_by_id(db, emp_id)
        if instance is None:
            return None
        for field, value in kwargs.items():
            setattr(instance, field, value)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def update_embedding(cls, db: Session, emp_id: str, embedding_bytes: bytes) -> Optional["Employee"]:
        """
        Cập nhật embedding vector khuôn mặt.

        Ví dụ:
            Employee.update_embedding(db, "NV001", embedding_bytes)
        """
        return cls.update(db, emp_id, embedding=embedding_bytes)

    @classmethod
    def update_avatar(cls, db: Session, emp_id: str, paths: list[str]) -> Optional["Employee"]:
        """
        Cập nhật danh sách đường dẫn ảnh.

        Ví dụ:
            Employee.update_avatar(db, "NV001", ["dataset/NV001/01.jpg"])
        """
        return cls.update(db, emp_id, avatar_path=paths)

    # ==========================================================
    # DELETE
    # ==========================================================

    @classmethod
    def soft_delete(cls, db: Session, emp_id: str) -> bool:
        """
        Xóa mềm nhân viên (is_deleted=1), giữ lại lịch sử điểm danh.
        Trả về False nếu không tìm thấy.

        Ví dụ:
            Employee.soft_delete(db, "NV001")
        """
        instance = cls.get_active_by_id(db, emp_id)
        if instance is None:
            return False
        instance.is_deleted = 1
        db.commit()
        return True

    @classmethod
    def hard_delete(cls, db: Session, emp_id: str) -> bool:
        """
        Xóa cứng nhân viên khỏi database (không thể khôi phục).
        Trả về False nếu không tìm thấy.

        Ví dụ:
            Employee.hard_delete(db, "NV001")
        """
        instance = db.get(cls, emp_id)
        if instance is None:
            return False
        db.delete(instance)
        db.commit()
        return True

    # ==========================================================
    # HELPERS
    # ==========================================================

    def __repr__(self) -> str:
        return f"<Employee emp_id={self.emp_id!r} name={self.name!r}>"

    def to_dict(self) -> dict:
        return {
            "emp_id":      self.emp_id,
            "name":        self.name,
            "age":         self.age,
            "gender":      self.gender,
            "height":      float(self.height) if self.height else None,
            "weight":      float(self.weight) if self.weight else None,
            "avatar_path": self.avatar_path,
            "is_deleted":  self.is_deleted,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "updated_at":  self.updated_at.isoformat() if self.updated_at else None,
        }
