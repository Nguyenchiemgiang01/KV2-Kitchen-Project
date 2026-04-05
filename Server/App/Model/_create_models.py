from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import URL

from all_models import meal_list, user, employee, attendance_log
from all_models.base import Base
 
url = URL.create(
    "mysql+pymysql",
    username="root",
    password="Ncgncg1102@",
    host="localhost",
    port=3306,
    database="kitchen_project"
)

engine = create_engine(url)

try:
    with engine.connect() as connection:
        print("✅ Kết nối database thành công!")
except Exception as e:
    print("❌ Kết nối thất bại:")
    print(e)


print("model create", Base.metadata.tables.keys())
# tạo table
Base.metadata.create_all(engine)