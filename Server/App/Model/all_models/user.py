"""
============================================================
  models/user.py
  Model: User — Tài khoản và phân quyền hệ thống
============================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Enum, DateTime,
    ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship, Session

from .base import Base


class User(Base):
    """Tài khoản và phân quyền hệ thống."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_username"),
        Index("idx_role",      "role"),
        Index("idx_is_active", "is_active"),
        {
            "mysql_engine":         "InnoDB",
            "mysql_charset":        "utf8mb4",
            "mysql_collate":        "utf8mb4_unicode_ci",
            "mysql_auto_increment": "1",
            "comment":              "Tài khoản và phân quyền hệ thống",
        },
    )

    # ----------------------------------------------------------
    # COLUMNS
    # ----------------------------------------------------------

    id         = Column(Integer,    primary_key=True, autoincrement=True,        comment="ID tự tăng")
    emp_id     = Column(String(50), ForeignKey("employees.emp_id"), nullable=True, comment="Mã nhân viên liên kết")
    username   = Column(String(100), nullable=False,                             comment="Tên đăng nhập — duy nhất")
    password   = Column(String(255), nullable=False,                             comment="Mật khẩu đã hash (bcrypt)")
    full_name  = Column(String(200), nullable=True,                              comment="Họ và tên người dùng")
    role       = Column(
                    Enum("admin", "sub_admin", "manager_kitchen", "user"),
                    nullable=False, default="user",
                    comment="Phân quyền: admin | sub_admin | manager_kitchen | user",
                )
    is_active  = Column(TINYINT(1),  nullable=False, default=1,                  comment="Trạng thái: 1 = hoạt động, 0 = bị khóa")
    created_at = Column(DateTime,    default=datetime.now,                        comment="Thời điểm tạo tài khoản")
    updated_at = Column(DateTime,    default=datetime.now, onupdate=datetime.now, comment="Thời điểm cập nhật gần nhất")
    last_login = Column(DateTime,    nullable=True,                               comment="Thời điểm đăng nhập gần nhất")

    # ----------------------------------------------------------
    # RELATIONSHIPS
    # ----------------------------------------------------------

    employee = relationship("Employee", back_populates="user")

    # ==========================================================
    # SELECT
    # ==========================================================

    @classmethod
    def get_by_id(cls, db: Session, user_id: int) -> Optional["User"]:
        """
        Lấy user theo id.

        Ví dụ:
            user = User.get_by_id(db, 1)
        """
        return db.get(cls, user_id)

    @classmethod
    def get_by_username(cls, db: Session, username: str) -> Optional["User"]:
        """
        Lấy user theo username (dùng khi đăng nhập).

        Ví dụ:
            user = User.get_by_username(db, "nv001")
        """
        return db.query(cls).filter(cls.username == username).first()

    @classmethod
    def get_all(cls, db: Session) -> list["User"]:
        """
        Lấy tất cả user đang hoạt động.

        Ví dụ:
            users = User.get_all(db)
        """
        return db.query(cls).filter(cls.is_active == 1).all()

    @classmethod
    def get_by_role(cls, db: Session, role: str) -> list["User"]:
        """
        Lấy danh sách user theo role.

        Ví dụ:
            admins = User.get_by_role(db, "admin")
        """
        return (
            db.query(cls)
            .filter(cls.role == role, cls.is_active == 1)
            .all()
        )

    @classmethod
    def get_by_emp_id(cls, db: Session, emp_id: str) -> Optional["User"]:
        """
        Lấy tài khoản liên kết với một nhân viên.

        Ví dụ:
            user = User.get_by_emp_id(db, "NV001")
        """
        return db.query(cls).filter(cls.emp_id == emp_id).first()

    # ==========================================================
    # CREATE
    # ==========================================================

    @classmethod
    def create(cls, db: Session, **kwargs) -> "User":
        """
        Tạo tài khoản mới.

        Ví dụ:
            user = User.create(
                db,
                username  = "nv001",
                password  = hashed_pw,
                full_name = "Nguyễn Văn An",
                role      = "user",
                emp_id    = "NV001",
            )
        """
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    # ==========================================================
    # UPDATE
    # ==========================================================

    @classmethod
    def update(cls, db: Session, user_id: int, **kwargs) -> Optional["User"]:
        """
        Cập nhật thông tin user theo id.
        Trả về None nếu không tìm thấy.

        Ví dụ:
            User.update(db, 1, full_name="Tên Mới", role="sub_admin")
        """
        instance = db.get(cls, user_id)
        if instance is None:
            return None
        for field, value in kwargs.items():
            setattr(instance, field, value)
        db.commit()
        db.refresh(instance)
        return instance

    @classmethod
    def update_password(cls, db: Session, user_id: int, hashed_password: str) -> Optional["User"]:
        """
        Cập nhật mật khẩu (truyền vào giá trị đã hash).

        Ví dụ:
            User.update_password(db, 1, bcrypt.hash("new_pass"))
        """
        return cls.update(db, user_id, password=hashed_password)

    @classmethod
    def update_role(cls, db: Session, user_id: int, role: str) -> Optional["User"]:
        """
        Thay đổi phân quyền user.

        Ví dụ:
            User.update_role(db, 1, "admin")
        """
        return cls.update(db, user_id, role=role)

    @classmethod
    def record_login(cls, db: Session, user_id: int) -> Optional["User"]:
        """
        Ghi nhận thời điểm đăng nhập gần nhất.

        Ví dụ:
            User.record_login(db, 1)
        """
        return cls.update(db, user_id, last_login=datetime.now())

    # ==========================================================
    # DELETE
    # ==========================================================

    @classmethod
    def deactivate(cls, db: Session, user_id: int) -> bool:
        """
        Khóa tài khoản (is_active=0) thay vì xóa cứng.
        Trả về False nếu không tìm thấy.

        Ví dụ:
            User.deactivate(db, 1)
        """
        instance = db.get(cls, user_id)
        if instance is None:
            return False
        instance.is_active = 0
        db.commit()
        return True

    @classmethod
    def activate(cls, db: Session, user_id: int) -> bool:
        """
        Mở khóa tài khoản.
        Trả về False nếu không tìm thấy.

        Ví dụ:
            User.activate(db, 1)
        """
        instance = db.get(cls, user_id)
        if instance is None:
            return False
        instance.is_active = 1
        db.commit()
        return True

    @classmethod
    def hard_delete(cls, db: Session, user_id: int) -> bool:
        """
        Xóa cứng tài khoản khỏi database.
        Trả về False nếu không tìm thấy.

        Ví dụ:
            User.hard_delete(db, 1)
        """
        instance = db.get(cls, user_id)
        if instance is None:
            return False
        db.delete(instance)
        db.commit()
        return True

    # ==========================================================
    # HELPERS
    # ==========================================================

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "emp_id":     self.emp_id,
            "username":   self.username,
            "full_name":  self.full_name,
            "role":       self.role,
            "is_active":  self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
