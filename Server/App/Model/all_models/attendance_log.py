"""
============================================================
  models/attendance_log.py
  Model: AttendanceLog — Lịch sử nhận diện khuôn mặt
============================================================
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import relationship, Session

from .base import Base

from all_models import employee , user, meal_list

class AttendanceLog(Base):
    """Lịch sử nhận diện khuôn mặt."""

    __tablename__ = "attendance_log"
    __table_args__ = (
        Index("idx_log_date",      "log_date"),
        Index("idx_log_emp_id",    "emp_id"),
        Index("idx_log_status",    "status"),
        Index("idx_log_timestamp", "timestamp"),
        {
            "mysql_engine":         "InnoDB",
            "mysql_charset":        "utf8mb4",
            "mysql_collate":        "utf8mb4_unicode_ci",
            "mysql_auto_increment": "1",
            "comment":              "Lịch sử nhận diện khuôn mặt",
        },
    )

    # ----------------------------------------------------------
    # COLUMNS
    # ----------------------------------------------------------

    id         = Column(Integer,    primary_key=True, autoincrement=True, comment="ID tự tăng")
    emp_id     = Column(String(50), ForeignKey("employees.emp_id"), nullable=True, comment="Mã nhân viên — NULL nếu không nhận ra")
    name       = Column(String(200), nullable=True,                  comment="Tên nhân viên tại thời điểm nhận diện")
    log_date   = Column(Date,        nullable=False,                  comment="Ngày điểm danh")
    timestamp  = Column(DateTime,    default=datetime.now,            comment="Thời điểm nhận diện chính xác")
    status     = Column(String(20),  nullable=False,                  comment="valid | invalid | not_registered | no_face")
    similarity = Column(Float,       nullable=True,                   comment="Điểm cosine similarity (0.0 – 1.0)")

    # ----------------------------------------------------------
    # RELATIONSHIPS
    # ----------------------------------------------------------

    employee = relationship("Employee", back_populates="attendance_logs")

    # ==========================================================
    # SELECT
    # ==========================================================

    @classmethod
    def get_by_id(cls, db: Session, log_id: int) -> Optional["AttendanceLog"]:
        """
        Lấy một bản ghi log theo id.

        Ví dụ:
            log = AttendanceLog.get_by_id(db, 10)
        """
        return db.get(cls, log_id)

    @classmethod
    def get_by_date(cls, db: Session, log_date: date) -> list["AttendanceLog"]:
        """
        Lấy toàn bộ log điểm danh trong một ngày.

        Ví dụ:
            logs = AttendanceLog.get_by_date(db, date(2024, 1, 15))
        """
        return db.query(cls).filter(cls.log_date == log_date).all()

    @classmethod
    def get_by_emp(cls, db: Session, emp_id: str) -> list["AttendanceLog"]:
        """
        Lấy toàn bộ lịch sử điểm danh của một nhân viên.

        Ví dụ:
            logs = AttendanceLog.get_by_emp(db, "NV001")
        """
        return db.query(cls).filter(cls.emp_id == emp_id).all()

    @classmethod
    def get_by_emp_and_date(cls, db: Session, emp_id: str, log_date: date) -> list["AttendanceLog"]:
        """
        Lấy log điểm danh của nhân viên trong một ngày cụ thể.

        Ví dụ:
            logs = AttendanceLog.get_by_emp_and_date(db, "NV001", date.today())
        """
        return (
            db.query(cls)
            .filter(cls.emp_id == emp_id, cls.log_date == log_date)
            .all()
        )

    @classmethod
    def get_by_status(cls, db: Session, status: str, log_date: Optional[date] = None) -> list["AttendanceLog"]:
        """
        Lấy log theo trạng thái, có thể lọc thêm theo ngày.

        Ví dụ:
            AttendanceLog.get_by_status(db, "valid", date.today())
            AttendanceLog.get_by_status(db, "no_face")
        """
        query = db.query(cls).filter(cls.status == status)
        if log_date:
            query = query.filter(cls.log_date == log_date)
        return query.all()

    @classmethod
    def get_today(cls, db: Session) -> list["AttendanceLog"]:
        """
        Lấy toàn bộ log điểm danh hôm nay.

        Ví dụ:
            logs = AttendanceLog.get_today(db)
        """
        return cls.get_by_date(db, date.today())

    # ==========================================================
    # CREATE
    # ==========================================================

    @classmethod
    def create(cls, db: Session, **kwargs) -> "AttendanceLog":
        """
        Ghi nhận một lần nhận diện khuôn mặt.

        Ví dụ:
            AttendanceLog.create(
                db,
                emp_id     = "NV001",
                name       = "Nguyễn Văn An",
                log_date   = date.today(),
                status     = "valid",
                similarity = 0.97,
            )
        """
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def log_recognition(
        cls,
        db: Session,
        status: str,
        emp_id: Optional[str] = None,
        name: Optional[str] = None,
        similarity: Optional[float] = None,
    ) -> "AttendanceLog":
        """
        Shortcut ghi log nhận diện — tự động điền log_date và timestamp.

        Ví dụ:
            # Nhận diện thành công
            AttendanceLog.log_recognition(db, "valid", emp_id="NV001", name="An", similarity=0.96)

            # Không nhận ra khuôn mặt
            AttendanceLog.log_recognition(db, "no_face")
        """
        now = datetime.now()
        return cls.create(
            db,
            emp_id=emp_id,
            name=name,
            log_date=now.date(),
            timestamp=now,
            status=status,
            similarity=similarity,
        )

    # ==========================================================
    # UPDATE
    # ==========================================================

    @classmethod
    def update(cls, db: Session, log_id: int, **kwargs) -> Optional["AttendanceLog"]:
        """
        Cập nhật một bản ghi log theo id.
        Dùng khi cần hiệu chỉnh thủ công.
        Trả về None nếu không tìm thấy.

        Ví dụ:
            AttendanceLog.update(db, 10, status="valid", similarity=0.95)
        """
        instance = db.get(cls, log_id)
        if instance is None:
            return None
        for field, value in kwargs.items():
            setattr(instance, field, value)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def update_status(cls, db: Session, log_id: int, status: str) -> Optional["AttendanceLog"]:
        """
        Chỉnh sửa trạng thái của một bản ghi log.

        Ví dụ:
            AttendanceLog.update_status(db, 10, "invalid")
        """
        return cls.update(db, log_id, status=status)

    @classmethod
    def update_similarity(cls, db: Session, log_id: int, similarity: float) -> Optional["AttendanceLog"]:
        """
        Cập nhật lại điểm similarity sau khi tính toán lại.

        Ví dụ:
            AttendanceLog.update_similarity(db, 10, 0.98)
        """
        return cls.update(db, log_id, similarity=similarity)

    # ==========================================================
    # DELETE
    # ==========================================================

    @classmethod
    def delete_by_id(cls, db: Session, log_id: int) -> bool:
        """
        Xóa một bản ghi log theo id.
        Trả về False nếu không tìm thấy.

        Ví dụ:
            AttendanceLog.delete_by_id(db, 10)
        """
        instance = db.get(cls, log_id)
        if instance is None:
            return False
        db.delete(instance)
        db.commit()
        return True

    @classmethod
    def delete_by_date(cls, db: Session, log_date: date) -> int:
        """
        Xóa toàn bộ log trong một ngày.
        Trả về số bản ghi đã xóa.

        Ví dụ:
            count = AttendanceLog.delete_by_date(db, date(2024, 1, 15))
        """
        count = db.query(cls).filter(cls.log_date == log_date).delete()
        db.commit()
        return count

    @classmethod
    def delete_by_emp_and_date(cls, db: Session, emp_id: str, log_date: date) -> int:
        """
        Xóa toàn bộ log của một nhân viên trong ngày cụ thể.
        Trả về số bản ghi đã xóa.

        Ví dụ:
            count = AttendanceLog.delete_by_emp_and_date(db, "NV001", date.today())
        """
        count = (
            db.query(cls)
            .filter(cls.emp_id == emp_id, cls.log_date == log_date)
            .delete()
        )
        db.commit()
        return count

    # ==========================================================
    # HELPERS
    # ==========================================================

    def __repr__(self) -> str:
        return (
            f"<AttendanceLog id={self.id} emp_id={self.emp_id!r} "
            f"status={self.status!r} similarity={self.similarity}>"
        )

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "emp_id":     self.emp_id,
            "name":       self.name,
            "log_date":   self.log_date.isoformat() if self.log_date else None,
            "timestamp":  self.timestamp.isoformat() if self.timestamp else None,
            "status":     self.status,
            "similarity": self.similarity,
        }
