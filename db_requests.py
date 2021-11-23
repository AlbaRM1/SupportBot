import sqlite3


def createBD_FromDump():
    cur = sqlite3.connect('db/db.db')
    f = open('db/db_dump.sql', 'r', encoding='UTF-8')
    dump = f.read()
    cur.executescript(dump)


class requestDB:

    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES(?) ", (user_id,))

    def get_users(self):
        with self.connection:
            self.cursor.execute("SELECT * FROM `users`")
            return self.cursor.fetchall()

    def get_chatID_by_userID(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT chat_id FROM `users` WHERE user_id=?", (user_id,))
            return self.cursor.fetchone()

    def get_operators(self):
        with self.connection:
            self.cursor.execute("SELECT user_id FROM `operators`")
            return self.cursor.fetchall()

    def get_free_operators(self):
        with self.connection:
            self.cursor.execute(
                "SELECT user_id FROM `operators` WHERE status=True")
            return self.cursor.fetchall()

    def oper_getStatus(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT status FROM operators WHERE user_id=?", (user_id,))
            return (self.cursor.fetchall())[0][0]

    def oper_setStatus(self, user_id, value):
        with self.connection:
            return self.cursor.execute(
                "UPDATE operators SET status=? WHERE user_id=?", (value, user_id))

    def add_dialogue(self, operator_id, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `dialogs` (`operator_id`, `user_id`) VALUES(?, ?) ", (operator_id, user_id))

    def get_dialogs(self):
        with self.connection:
            self.cursor.execute("SELECT * FROM `dialogs`")
            return self.cursor.fetchall()

    def get_dialogue(self, user_id):
        with self.connection:
            self.cursor.execute(
                "SELECT * FROM dialogs WHERE operator_id=? OR user_id=?", (user_id, user_id))
            return self.cursor.fetchone()

    def delete_dialogue(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `dialogs` WHERE operator_id=? OR user_id=?", (user_id, user_id))

    def delete_user(self, user_id):
        with self.connection:
            self.cursor.execute(
                "DELETE FROM `users` WHERE user_id=?", (user_id,))

    def delete_operator(self, operator_id):
        with self.connection:
            self.cursor.execute(
                "DELETE FROM `operators` WHERE user_id=?", (operator_id,))

    def ban_user(self, user_id):
        with self.connection:
            self.cursor.execute(
                "INSERT INTO `blocklist` (`user_id`) VALUES(?) ", (user_id,))

    def unblock_user(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM `blocklist` WHERE user_id=?", (user_id,))

    def get_users_in_blocklist(self):
        with self.connection:
            self.cursor.execute("SELECT * FROM `blocklist`")
            return self.cursor.fetchall()

    def add_ticket_to_db(self, sender_id, sender_first_name, text=None, file=None, content_type=None):
        with self.connection:
            return self.cursor.execute("INSERT INTO `tickets` (`sender_id`, 'first_name', 'text', 'file', 'content_type') VALUES(?,?,?,?,?) ", (sender_id, sender_first_name, text, file, content_type))

    def get_all_tickets(self):
        with self.connection:
            self.cursor.execute("SELECT * FROM `tickets`")
            return self.cursor.fetchall()

    def delete_ticket(self, sender_id):
        with self.connection:
            self.cursor.execute(
                "DELETE FROM `tickets` WHERE sender_id=?", (sender_id,))

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
