import sqlite3
import contextlib

class QueryExecutor:

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def create_db_not_exists(self) -> None:
        with contextlib.closing(sqlite3.connect(self.filename)) as connection:
            connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )
            ''')
            connection.commit()

    def insert_user(self, username: str, password: str) -> bool:
        try:
            with contextlib.closing(sqlite3.connect(self.filename)) as connection:
                connection.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                connection.commit()
            print("User added successfully.")
            return True
        except sqlite3.IntegrityError:
            print("The username already exists. Please enter a different username.")    
            return False
        
    def remove_user(self, username: str, password: str) -> bool:
        with contextlib.closing(sqlite3.connect(self.filename)) as connection:
            result = connection.execute(
                'DELETE FROM users WHERE username = ? AND password = ?', 
                (username, password)
            )
            connection.commit()

            if result.rowcount > 0:
                print("User deleted successfully.")
                return True
            else:
                print("Username not found.")
                return False

    def login(self, username: str, password: str) -> bool:
        with contextlib.closing(sqlite3.connect(self.filename)) as connection:
            result = connection.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?', 
                (username, password)
            )
            return result.fetchone() is not None
        
    def user_exists(self, username: str) -> bool:
        with contextlib.closing(sqlite3.connect(self.filename)) as connection:
            result = connection.execute(
                'SELECT * FROM users WHERE username = ?', 
                (username,)
            )
            return result.fetchone() is not None
