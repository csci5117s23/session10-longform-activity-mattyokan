import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import ThreadedConnectionPool


class Database(object):
    def __init__(self):
        DATABASE_URL = os.environ['DATABASE_URL']
        self.pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL)
        self.setup_table()

    @contextmanager
    def get_db_connection(self):
        try:
            connection = self.pool.getconn()
            yield connection
        finally:
            self.pool.putconn(connection)

    @contextmanager
    def get_db_cursor(self, commit=False):
        with self.get_db_connection() as connection:
            cursor = connection.cursor(cursor_factory=DictCursor)
            # cursor = connection.cursor()
            try:
                yield cursor
                if commit:
                    connection.commit()
            finally:
                cursor.close()

    def setup_table(self):
        with self.get_db_cursor(True) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users(
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(500) -- Not a great idea as an identifier, should ideally use the JWT info from oauth, but oh well
                );
                
                CREATE INDEX IF NOT EXISTS email ON Users USING HASH (email);  
            """)

    def recordLogin(self, email):
        # This is not atomic but it will have to work
        with self.get_db_cursor(True) as cursor:
            cursor.execute("""
                SELECT id FROM Users where email = (%(user)s)
            """, {'user': email })
            creation_result = cursor.fetchone()
            if creation_result is None:
                cursor.execute("""
                    INSERT INTO Users (email) VALUES (%(user)s)
                """, {'user': email})
            else:
                return creation_result[0]