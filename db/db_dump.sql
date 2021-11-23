-- Использованная кодировка текста: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Таблица: blocklist
CREATE TABLE blocklist (user_id INTEGER UNIQUE NOT NULL);

-- Таблица: dialogs
CREATE TABLE dialogs (operator_id INTEGER UNIQUE NOT NULL, user_id INTEGER UNIQUE NOT NULL);

-- Таблица: operators
CREATE TABLE operators (user_id INTEGER UNIQUE NOT NULL, status BOOLEAN NOT NULL DEFAULT (False));

-- Таблица: tickets
CREATE TABLE tickets (sender_id INTEGER NOT NULL, first_name CHAR NOT NULL, text CHAR DEFAULT None, file CHAR DEFAULT None, content_type CHAR NOT NULL);

-- Таблица: users
CREATE TABLE users (user_id INTEGER NOT NULL UNIQUE);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
