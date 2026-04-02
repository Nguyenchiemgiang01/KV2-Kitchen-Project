import os
import numpy as np
from sqlalchemy.orm import Session
from app.core.face_engine import face_engine
from app.models.employee import Employee


def register_employee(
    session: Session,
    emp_id: str,
    name: str,
    image_paths: list,
    min_valid_images: int = 3
) -> dict:

    embeddings = []
    failed     = []
    skipped    = []

    for path in image_paths:
        if not os.path.exists(path):
            skipped.append(path)
            continue

        embedding = face_engine.get_embedding_from_path(path)

        if embedding is None:
            failed.append(os.path.basename(path))
            continue

        embeddings.append(embedding)

    if len(embeddings) < min_valid_images:
        raise ValueError(
            f"Chỉ detect được {len(embeddings)}/{len(image_paths)} ảnh hợp lệ "
            f"(cần ít nhất {min_valid_images}). Kiểm tra lại chất lượng ảnh."
        )

    avg_embedding = np.mean(embeddings, axis=0).astype(np.float32)

    emp = session.get(Employee, emp_id)
    if emp is None:
        emp = Employee(emp_id=emp_id, name=name)
        session.add(emp)
        action = "Đăng ký mới"
    else:
        emp.name = name
        action = "Cập nhật"

    emp.set_embedding(avg_embedding)
    session.commit()

    return {
        "action"        : action,
        "emp_id"        : emp_id,
        "name"          : name,
        "total_images"  : len(image_paths),
        "valid_images"  : len(embeddings),
        "failed_images" : failed,
        "skipped_images": skipped,
        "status"        : "success"
    }


def delete_employee(session: Session, emp_id: str) -> dict:
    emp = session.get(Employee, emp_id)
    if emp is None:
        raise ValueError(f"Không tìm thấy nhân viên ID: {emp_id}")
    session.delete(emp)
    session.commit()
    return {"emp_id": emp_id, "status": "deleted"}


def get_all_employees(session: Session) -> list:
    return session.query(Employee).all()