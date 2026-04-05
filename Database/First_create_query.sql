-- ============================================================
--  FACE RECOGNITION SYSTEM — DATABASE SETUP
--  Chạy toàn bộ file này trong MySQL Workbench hoặc terminal
-- ============================================================


-- ------------------------------------------------------------
-- TẠO DATABASE
-- ------------------------------------------------------------

USE kitchen_project;


-- ------------------------------------------------------------
--  1. BẢNG NHÂN VIÊN
--     Lưu thông tin và embedding vector khuôn mặt
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    emp_id      VARCHAR(50)             NOT NULL                    COMMENT 'Mã nhân viên — khóa chính',
    name        VARCHAR(200)            NOT NULL                    COMMENT 'Họ và tên nhân viên',
    age         TINYINT                 NULL                        COMMENT 'Tuổi nhân viên',
    gender      ENUM('Nam','Nữ','Khác') NULL                        COMMENT 'Giới tính',
    height      DECIMAL(5,2)            NULL                        COMMENT 'Chiều cao (cm) — ví dụ: 170.50',
    weight      DECIMAL(5,2)            NULL                        COMMENT 'Cân nặng (kg) — ví dụ: 65.00',
    avatar_path JSON                    NULL                        COMMENT 'Danh sách đường dẫn ảnh — ["dataset/NV001/01.jpg","dataset/NV001/02.jpg"]',
    embedding   LONGBLOB                NULL                    COMMENT 'Embedding vector 512-D (numpy array serialized)',
	is_deleted  TINYINT(1)              NOT NULL DEFAULT 0          COMMENT 'Soft delete: 0 = đang hoạt động, 1 = đã xóa',
    created_at  DATETIME                DEFAULT CURRENT_TIMESTAMP   COMMENT 'Thời điểm đăng ký lần đầu',
    updated_at  DATETIME                DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP COMMENT 'Thời điểm cập nhật gần nhất',

    PRIMARY KEY (emp_id)
)   ENGINE  = InnoDB
    DEFAULT CHARSET  = utf8mb4
    COLLATE = utf8mb4_unicode_ci
    COMMENT = 'Danh sách nhân viên và embedding khuôn mặt';

-- ------------------------------------------------------------
--  2.BẢNG USER — Tài khoản và phân quyền hệ thống
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          INT                                                     NOT NULL AUTO_INCREMENT         COMMENT 'ID tự tăng',
	emp_id      VARCHAR(50)                                             NULL ,
    username    VARCHAR(100)                                            NOT NULL                        COMMENT 'Tên đăng nhập — duy nhất',
    password    VARCHAR(255)                                            NOT NULL                        COMMENT 'Mật khẩu đã hash (bcrypt)',
    full_name   VARCHAR(200)                                            NULL                            COMMENT 'Họ và tên người dùng',
    role        ENUM('admin','sub_admin','manager_kitchen','user')      NOT NULL DEFAULT 'user'         COMMENT 'Phân quyền: admin | sub_admin | manager_kitchen | user',
    is_active   TINYINT(1)                                              NOT NULL DEFAULT 1              COMMENT 'Trạng thái: 1 = đang hoạt động, 0 = bị khóa',
    created_at  DATETIME                                                DEFAULT CURRENT_TIMESTAMP       COMMENT 'Thời điểm tạo tài khoản',
    updated_at  DATETIME                                                DEFAULT CURRENT_TIMESTAMP
                                                                        ON UPDATE CURRENT_TIMESTAMP     COMMENT 'Thời điểm cập nhật gần nhất',
    last_login  DATETIME                                                NULL                            COMMENT 'Thời điểm đăng nhập gần nhất',

    PRIMARY KEY (id),
    UNIQUE  KEY uq_username     (username),
    INDEX   idx_role            (role),
    INDEX   idx_is_active       (is_active),
    
	CONSTRAINT fk_user_emp
        FOREIGN KEY (emp_id)
        REFERENCES  employees (emp_id)
)   ENGINE  = InnoDB
    AUTO_INCREMENT = 1
    DEFAULT CHARSET  = utf8mb4
    COLLATE = utf8mb4_unicode_ci
    COMMENT = 'Tài khoản và phân quyền hệ thống';
    
-- ------------------------------------------------------------
--  3. BẢNG DANH SÁCH ĐĂNG KÝ ĂN
--     Mỗi hàng = một nhân viên được phép ăn trong một ngày
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meal_list (
    id          INT             NOT NULL AUTO_INCREMENT          COMMENT 'ID tự tăng',
    emp_id      VARCHAR(50)     NOT NULL                         COMMENT 'Mã nhân viên',
    meal_date   DATE            NOT NULL                         COMMENT 'Ngày đăng ký ăn',
    created_at  DATETIME        DEFAULT CURRENT_TIMESTAMP        COMMENT 'Thời điểm tạo bản ghi',

    PRIMARY KEY (id),
    INDEX   idx_meal_date        (meal_date),
    INDEX   idx_meal_emp_id      (emp_id),
    
	CONSTRAINT fk_meal_emp
		FOREIGN KEY (emp_id)
		REFERENCES  employees (emp_id)
    
)   ENGINE  = InnoDB
    AUTO_INCREMENT = 1
    DEFAULT CHARSET  = utf8mb4
    COLLATE = utf8mb4_unicode_ci
    COMMENT = 'Danh sách nhân viên đăng ký ăn theo ngày';

-- ------------------------------------------------------------
--  4. BẢNG LOG ĐIỂM DANH
--     Ghi lại mỗi lần nhận diện xảy ra
--     emp_id KHÔNG dùng foreign key cứng → giữ lịch sử
--     ngay cả khi nhân viên đã bị xóa khỏi hệ thống
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance_log (
    id          INT             NOT NULL AUTO_INCREMENT          COMMENT 'ID tự tăng',
    emp_id      VARCHAR(50)     NULL                             COMMENT 'Mã nhân viên — khóa ngoại (NULL nếu không nhận ra)',
    name        VARCHAR(200)    NULL                             COMMENT 'Tên nhân viên tại thời điểm nhận diện',
    log_date    DATE            NOT NULL                         COMMENT 'Ngày điểm danh',
    timestamp   DATETIME        DEFAULT CURRENT_TIMESTAMP        COMMENT 'Thời điểm nhận diện chính xác',
    status      VARCHAR(20)     NOT NULL                         COMMENT 'valid | invalid | not_registered | no_face',
    similarity  FLOAT           NULL                             COMMENT 'Điểm cosine similarity (0.0 – 1.0)',

    PRIMARY KEY (id),
    INDEX   idx_log_date        (log_date),
    INDEX   idx_log_emp_id      (emp_id),
    INDEX   idx_log_status      (status),
    INDEX   idx_log_timestamp   (timestamp),

    CONSTRAINT fk_log_emp
        FOREIGN KEY (emp_id)
        REFERENCES  employees (emp_id)
)   ENGINE  = InnoDB
    AUTO_INCREMENT = 1
    DEFAULT CHARSET  = utf8mb4
    COLLATE = utf8mb4_unicode_ci
    COMMENT = 'Lịch sử nhận diện khuôn mặt';