from app.db.session import engine, Base
from app.models.employee import Employee  # noqa


def init_db():
    print("Đang tạo bảng database...")
    Base.metadata.create_all(bind=engine)
    print("Tạo bảng thành công.")


if __name__ == "__main__":
    init_db()