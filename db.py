import sqlite3
import markups


class Database:

    def __init__(self, db_path: str) -> None:

        self.db_path = db_path
        try:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.execute('PRAGMA foreign_keys = 1')
        except Exception as e:
            print(e.__str__())

        self._cursor = self._connection.cursor()
        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS admins(admin_id INT PRIMARY KEY)')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS users('
                                 'user_id INT, '
                                 'username TEXT, '
                                 'msg_count INT DEFAULT 0, '
                                 'last_msg_date TEXT DEFAULT NULL, '
                                 'PRIMARY KEY(user_id) '
                                 ')')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS rewards('
                                 'user_id INT, '
                                 'promo_5 TEXT DEFAULT NULL, '
                                 'promo_10 TEXT DEFAULT NULL, '
                                 'promo_15 TEXT DEFAULT NULL, '
                                 'promo_20 TEXT DEFAULT NULL, '
                                 'promo_25 TEXT DEFAULT NULL, '
                                 'PRIMARY KEY(user_id), '
                                 'FOREIGN KEY(user_id) REFERENCES users(user_id)'
                                 ')')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS promocodes(promocode TEXT PRIMARY KEY, level INT)')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS localisations('
                                 'localisation TEXT PRIMARY KEY, '
                                 'lvl_up_text TEXT, '
                                 'status_up_text TEXT, '
                                 'leaderboard_text TEXT'
                                 ')')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS chats('
                                 'chat_id INT PRIMARY KEY, '
                                 'localisation TEXT DEFAULT \'en\' REFERENCES localisations(localisation) '
                                 'ON DELETE SET DEFAULT'
                                 ')')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS leaderboard('
                                 'chat_id INT, '
                                 'user_id INT, '
                                 'username TEXT, '
                                 'msg_count INT DEFAULT 0, '
                                 'PRIMARY KEY(chat_id, user_id)'
                                 ')')

        with self._connection:
            self._cursor.execute('CREATE TABLE IF NOT EXISTS chat_admins('
                                 'user_id INT PRIMARY KEY, '
                                 'username TEXT'
                                 ')')

        self.add_localisation('en', markups.lvl_up_text_eng, markups.status_up_text_eng, markups.leaderboard_text_eng)

    def add_chat_admin(self, user_id, username):
        with self._connection:
            self._cursor.execute('INSERT INTO chat_admins(user_id, username) VALUES(?, ?)', (user_id, username))
            return self._cursor.rowcount

    def get_chat_admins_ids(self):
        with self._connection:
            self._cursor.execute('SELECT user_id FROM chat_admins')
            res = self._cursor.fetchall()
            return [x[0] for x in res]

    def get_chat_admins(self):
        with self._connection:
            self._cursor.execute('SELECT * FROM chat_admins')
            return self._cursor.fetchall()

    def del_chat_admin(self, user_id):
        with self._connection:
            self._cursor.execute('DELETE FROM chat_admins WHERE user_id = ?', (user_id,))
            return self._cursor.rowcount

    def add_user_to_leaderboard(self, chat_id, user_id, username):
        with self._connection:
            self._cursor.execute('INSERT INTO leaderboard(chat_id, user_id, username) VALUES(?, ?, ?) '
                                 'ON CONFLICT DO NOTHING',
                                 (chat_id, user_id, username))

    def get_leaderboard(self):
        with self._connection:
            self._cursor.execute('SELECT * FROM leaderboard ORDER BY chat_id')
            return self._cursor.fetchall()

    def get_leaderboard_by_chat(self, chat_id):
        with self._connection:
            self._cursor.execute('SELECT * FROM leaderboard WHERE chat_id = ? ORDER BY chat_id', (chat_id,))
            return self._cursor.fetchall()

    def clear_leaderboard_by_chat_id(self, chat_id):
        with self._connection:
            self._cursor.execute('DELETE FROM leaderboard WHERE chat_id = ?', (chat_id,))

    def update_message_count_in_leaderboard(self, chat_id, user_id):
        with self._connection:
            self._cursor.execute('UPDATE leaderboard SET msg_count = msg_count + 1 WHERE user_id = ? AND chat_id = ?',
                                 (user_id, chat_id))

    def clear_leaderboard(self):
        with self._connection:
            self._cursor.execute('DELETE FROM leaderboard')

    def get_localisations(self):
        with self._connection:
            self._cursor.execute('SELECT * FROM localisations')
            return self._cursor.fetchall()

    def get_localisation(self, chat_id):
        with self._connection:
            self._cursor.execute('SELECT lvl_up_text, status_up_text, leaderboard_text FROM localisations '
                                 'INNER JOIN chats ON localisations.localisation = chats.localisation '
                                 'WHERE chat_id = ?', (chat_id,))
            res = self._cursor.fetchone()
            if res == ():
                return None
            return res

    def get_default_localisation(self):
        with self._connection:
            self._cursor.execute('SELECT lvl_up_text, status_up_text, leaderboard_text FROM localisations '
                                 'WHERE localisation = \'en\'')
            return self._cursor.fetchone()

    def add_localisation(self, loc, lvl_up_text, status_up_text, leaderboard_text):
        with self._connection:
            self._cursor.execute(
                'INSERT INTO localisations(localisation, lvl_up_text, status_up_text, leaderboard_text) '
                'VALUES(?, ?, ?, ?) ON CONFLICT DO NOTHING',
                (loc, lvl_up_text, status_up_text, leaderboard_text))

    def del_localisation(self, loc):
        with self._connection:
            self._cursor.execute('DELETE FROM localisations WHERE localisation = ?', (loc,))

    def add_chat(self, chat_id, loc):
        with self._connection:
            self._cursor.execute('INSERT INTO chats(chat_id, localisation) VALUES(?, ?)', (chat_id, loc))

    def get_chats(self):
        with self._connection:
            self._cursor.execute('SELECT * FROM chats')
            return self._cursor.fetchall()

    def del_chat(self, chat_id):
        with self._connection:
            self._cursor.execute('DELETE FROM chats WHERE chat_id = ?', (chat_id,))

    def get_admins(self):
        with self._connection:
            self._cursor.execute('SELECT * FROM admins')
            res = self._cursor.fetchall()
            return [x[0] for x in res]

    def add_admin(self, admin_id):
        with self._connection:
            self._cursor.execute('INSERT INTO admins(admin_id) VALUES(?) ON CONFLICT DO NOTHING', (admin_id,))

    def get_user_msg_count(self, user_id):
        with self._connection:
            self._cursor.execute('SELECT msg_count FROM users WHERE user_id = ?',
                                 (user_id,))
            return self._cursor.fetchone()[0]

    def get_user(self, user_id):
        with self._connection:
            self._cursor.execute('SELECT * FROM users WHERE user_id == ?', (user_id,))
            return self._cursor.fetchone()

    def add_user(self, user_id, username, last_message_date=None):
        with self._connection:
            self._cursor.execute('INSERT INTO users(user_id, username, last_msg_date) VALUES(?, ?, ?) '
                                 'ON CONFLICT(user_id) DO UPDATE SET username = EXCLUDED.username RETURNING last_msg_date',
                                 (user_id, username, last_message_date))
            last = self._cursor.fetchone()
            self._cursor.execute('INSERT INTO rewards(user_id) VALUES(?) ON CONFLICT DO NOTHING',
                                 (user_id,))

    def update_message_count(self, user_id, last_message_date):
        with self._connection:
            self._cursor.execute('UPDATE users SET msg_count = msg_count + 1, last_msg_date = ? '
                                 'WHERE user_id = ? AND msg_count < 750 '
                                 'RETURNING msg_count',
                                 (last_message_date, user_id))
            res = self._cursor.fetchone()
            return None if res is None else res[0]

    def get_last_message_date(self, user_id):
        with self._connection:
            self._cursor.execute('SELECT last_msg_date FROM users WHERE user_id = ?', (user_id,))
            return self._cursor.fetchone()[0]

    def get_user_promos(self, user_id):
        with self._connection:
            self._cursor.execute('SELECT msg_count, promo_5, promo_10, promo_15, promo_20, promo_25 FROM rewards '
                                 'INNER JOIN users ON users.user_id = rewards.user_id '
                                 'WHERE rewards.user_id = ?',
                                 (user_id,))
            return self._cursor.fetchone()

    def update_user_promos(self, user_id, promos):
        with self._connection:
            self._cursor.execute(
                'UPDATE rewards SET promo_5 = ?, promo_10 = ?, promo_15 = ?, promo_20 = ?, promo_25 = ? '
                'WHERE user_id = ?', (*promos, user_id))

    def add_promocode(self, promocode, level):
        with self._connection:
            self._cursor.execute('INSERT INTO promocodes(promocode, level) VALUES(?, ?) ON CONFLICT DO NOTHING',
                                 (promocode, level))
            return self._cursor.rowcount

    def set_language(self, user_id, language):
        with self._connection:
            self._cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))

    def get_promocode(self, level):
        with self._connection:
            self._cursor.execute('SELECT promocode FROM promocodes WHERE level = ? LIMIT 1', (level,))
            promo = self._cursor.fetchone()
            if promo is None:
                return None
            promo = promo[0]
            self._cursor.execute('DELETE FROM promocodes WHERE promocode = ?', (promo,))
            return promo

    def get_promocodes(self):
        with self._connection:
            self._cursor.execute('SELECT * FROM promocodes')
            return self._cursor.fetchall()

    def get_user_language(self, user_id):
        # useless now, made for multilanguage uses
        # was lazy to rewrite localisation machine :/
        return 'eng'

    def update_username_in_leaderboard(self, user_id, chat_id, new_username):
        with self._connection:
            self._cursor.execute('UPDATE leaderboard SET username = ? WHERE user_id = ? AND chat_id = ?',
                                 (new_username, user_id, chat_id))
            return self._cursor.rowcount
