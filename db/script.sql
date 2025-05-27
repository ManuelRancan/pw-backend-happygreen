-- Accedi a MySQL e crea il database
CREATE DATABASE pwhappygreen_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'happygreen_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON pwhappygreen_db.* TO 'happygreen_user'@'localhost';
FLUSH PRIVILEGES;