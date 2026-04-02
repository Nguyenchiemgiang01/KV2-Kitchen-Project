import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATASET_DIR
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.services.employee_service import register_employee

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def parse_folder_name(folder_name: str) -> tuple:
    parts = folder_name.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1].replace("_", " ")
    return folder_name, folder_name


def get_image_paths(folder_path: str) -> list:
    paths = []
    for fname in sorted(os.listdir(folder_path)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            paths.append(os.path.join(folder_path, fname))
    return paths


def main():
    init_db()
    session = SessionLocal()

    if not os.path.exists(DATASET_DIR):
        print(f"Không tìm thấy thư mục: {DATASET_DIR}")
        print("Tạo thư mục dataset/ và thêm ảnh nhân viên vào trước khi chạy.")
        return

    folders = sorted([
        f for f in os.listdir(DATASET_DIR)
        if os.path.isdir(os.path.join(DATASET_DIR, f))
    ])

    if not folders:
        print("Không có thư mục nhân viên nào trong dataset/")
        print("Cấu trúc cần: dataset/NV001_NguyenVanA/01.jpg ...")
        return

    print(f"Tìm thấy {len(folders)} nhân viên. Bắt đầu đăng ký...\n")
    print("=" * 55)

    success_count = 0
    failed_list   = []

    for folder in folders:
        folder_path  = os.path.join(DATASET_DIR, folder)
        emp_id, name = parse_folder_name(folder)
        image_paths  = get_image_paths(folder_path)

        if not image_paths:
            print(f"  [{folder}] Bỏ qua — không có ảnh nào.")
            continue

        print(f"  Nhân viên : {name}")
        print(f"  ID        : {emp_id}")
        print(f"  Số ảnh    : {len(image_paths)}")

        try:
            result = register_employee(session, emp_id, name, image_paths)
            print(f"  Kết quả   : {result['action']} thành công")
            print(f"  Hợp lệ    : {result['valid_images']}/{result['total_images']} ảnh")
            if result["failed_images"]:
                print(f"  Lỗi detect: {result['failed_images']}")
            success_count += 1
        except ValueError as e:
            print(f"  Lỗi       : {e}")
            failed_list.append(f"{name} ({emp_id})")

        print("-" * 55)

    session.close()

    print(f"\nHoàn tất: {success_count}/{len(folders)} nhân viên đăng ký thành công.")
    if failed_list:
        print(f"Thất bại  : {', '.join(failed_list)}")
    print("=" * 55)


if __name__ == "__main__":
    main()