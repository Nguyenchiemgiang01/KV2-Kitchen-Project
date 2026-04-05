"""
============================================================
  models/meal_list.py
  Model: MealList — Danh sách đăng ký ăn theo ngày
============================================================
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, Session

from .base import Base


class MealList(Base):
    """Danh sách nhân viên đăng ký ăn theo ngày."""

    __tablename__ = "meal_list"
    __table_args__ = (
        Index("idx_meal_date",   "meal_date"),
        Index("idx_meal_emp_id", "emp_id"),
        {
            "mysql_engine":         "InnoDB",
            "mysql_charset":        "utf8mb4",
            "mysql_collate":        "utf8mb4_unicode_ci",
            "mysql_auto_increment": "1",
            "comment":              "Danh sách nhân viên đăng ký ăn theo ngày",
        },
    )

    # ----------------------------------------------------------
    # COLUMNS
    # ----------------------------------------------------------

    id         = Column(Integer,     primary_key=True, autoincrement=True, comment="ID tự tăng")
    emp_id     = Column(String(50),  ForeignKey("employees.emp_id"), nullable=False, comment="Mã nhân viên")
    meal_date  = Column(Date,        nullable=False,                 comment="Ngày đăng ký ăn")
    created_at = Column(DateTime,    default=datetime.now,           comment="Thời điểm tạo bản ghi")

    # ----------------------------------------------------------
    # RELATIONSHIPS
    # ----------------------------------------------------------

    employee = relationship("Employee", back_populates="meal_list")

    # ==========================================================
    # SELECT
    # ==========================================================

    @classmethod
    def get_by_id(cls, db: Session, record_id: int) -> Optional["MealList"]:
        """
        Lấy bản ghi đăng ký ăn theo id.

        Ví dụ:
            meal = MealList.get_by_id(db, 5)
        """
        return db.get(cls, record_id)

    @classmethod
    def get_by_date(cls, db: Session, meal_date: date) -> list["MealList"]:
        """
        Lấy danh sách đăng ký ăn theo ngày.

        Ví dụ:
            meals = MealList.get_by_date(db, date(2024, 1, 15))
        """
        return db.query(cls).filter(cls.meal_date == meal_date).all()

    @classmethod
    def get_by_emp(cls, db: Session, emp_id: str) -> list["MealList"]:
        """
        Lấy toàn bộ lịch sử đăng ký ăn của một nhân viên.

        Ví dụ:
            meals = MealList.get_by_emp(db, "NV001")
        """
        return db.query(cls).filter(cls.emp_id == emp_id).all()

    @classmethod
    def get_by_emp_and_date(cls, db: Session, emp_id: str, meal_date: date) -> Optional["MealList"]:
        """
        Kiểm tra nhân viên đã đăng ký ăn ngày cụ thể chưa.

        Ví dụ:
            meal = MealList.get_by_emp_and_date(db, "NV001", date.today())
        """
        return (
            db.query(cls)
            .filter(cls.emp_id == emp_id, cls.meal_date == meal_date)
            .first()
        )

    @classmethod
    def get_today(cls, db: Session) -> list["MealList"]:
        """
        Lấy danh sách đăng ký ăn hôm nay.

        Ví dụ:
            meals = MealList.get_today(db)
        """
        return cls.get_by_date(db, date.today())

    # ==========================================================
    # CREATE
    # ==========================================================

    @classmethod
    def create(cls, db: Session, emp_id: str, meal_date: date) -> "MealList":
        """
        Tạo đăng ký ăn mới cho một nhân viên.

        Ví dụ:
            meal = MealList.create(db, emp_id="NV001", meal_date=date(2024, 1, 15))
        """
        instance = cls(emp_id=emp_id, meal_date=meal_date)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def register(cls, db: Session, emp_id: str, meal_date: date) -> Optional["MealList"]:
        """
        Đăng ký ăn — bỏ qua nếu nhân viên đã đăng ký trong ngày đó.
        Trả về None nếu bị trùng.

        Ví dụ:
            meal = MealList.register(db, "NV001", date.today())
        """
        if cls.get_by_emp_and_date(db, emp_id, meal_date):
            return None
        return cls.create(db, emp_id=emp_id, meal_date=meal_date)

    @classmethod
    def bulk_register(cls, db: Session, emp_ids: list[str], meal_date: date) -> list["MealList"]:
        """
        Đăng ký ăn hàng loạt cho nhiều nhân viên, bỏ qua nếu đã đăng ký.

        Ví dụ:
            MealList.bulk_register(db, ["NV001", "NV002", "NV003"], date.today())
        """
        existing_ids = {
            r.emp_id
            for r in db.query(cls.emp_id)
            .filter(cls.meal_date == meal_date)
            .all()
        }
        new_records = [
            cls(emp_id=eid, meal_date=meal_date)
            for eid in emp_ids
            if eid not in existing_ids
        ]
        if new_records:
            db.add_all(new_records)
            db.commit()
        return new_records

    # ==========================================================
    # UPDATE
    # ==========================================================

    @classmethod
    def update(cls, db: Session, record_id: int, **kwargs) -> Optional["MealList"]:
        """
        Cập nhật bản ghi đăng ký ăn theo id.
        Trả về None nếu không tìm thấy.

        Ví dụ:
            MealList.update(db, 5, meal_date=date(2024, 1, 20))
        """
        instance = db.get(cls, record_id)
        if instance is None:
            return None
        for field, value in kwargs.items():
            setattr(instance, field, value)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def update_date(cls, db: Session, record_id: int, new_date: date) -> Optional["MealList"]:
        """
        Thay đổi ngày đăng ký ăn.

        Ví dụ:
            MealList.update_date(db, 5, date(2024, 1, 20))
        """
        return cls.update(db, record_id, meal_date=new_date)

    # ==========================================================
    # DELETE
    # ==========================================================

    @classmethod
    def cancel(cls, db: Session, emp_id: str, meal_date: date) -> bool:
        """
        Hủy đăng ký ăn của nhân viên trong ngày cụ thể.
        Trả về False nếu không tìm thấy bản ghi.

        Ví dụ:
            MealList.cancel(db, "NV001", date.today())
        """
        instance = cls.get_by_emp_and_date(db, emp_id, meal_date)
        if instance is None:
            return False
        db.delete(instance)
        db.commit()
        return True

    @classmethod
    def delete_by_id(cls, db: Session, record_id: int) -> bool:
        """
        Xóa một bản ghi đăng ký ăn theo id.
        Trả về False nếu không tìm thấy.

        Ví dụ:
            MealList.delete_by_id(db, 5)
        """
        instance = db.get(cls, record_id)
        if instance is None:
            return False
        db.delete(instance)
        db.commit()
        return True

    @classmethod
    def delete_by_date(cls, db: Session, meal_date: date) -> int:
        """
        Xóa toàn bộ đăng ký ăn trong một ngày.
        Trả về số bản ghi đã xóa.

        Ví dụ:
            count = MealList.delete_by_date(db, date(2024, 1, 15))
        """
        count = db.query(cls).filter(cls.meal_date == meal_date).delete()
        db.commit()
        return count

    # ==========================================================
    # HELPERS
    # ==========================================================

    def __repr__(self) -> str:
        return f"<MealList id={self.id} emp_id={self.emp_id!r} meal_date={self.meal_date}>"

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "emp_id":     self.emp_id,
            "meal_date":  self.meal_date.isoformat() if self.meal_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
