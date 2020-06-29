"""
File: server_setup.py

This file creates / or resets the server database
"""

import sqlite3
import os

DATABASE_PATH = "server/db"


def main():
    will_reset = False
    if os.path.isfile(DATABASE_PATH):
        print("Database already exists. Do you want it reset? [NO]: ", end="")
        will_reset = input()
        if will_reset == "YES" or will_reset == "Yes" or will_reset == "yes":
            will_reset = True
            os.remove(DATABASE_PATH)
        else:
            will_reset = False

    if will_reset:
        db = sqlite3.connect(DATABASE_PATH)
        cursor = db.cursor()

        # Create tables
        cursor.execute('''
        CREATE TABLE server_settings(id INTEGER PRIMARY KEY, address TEXT, port INTEGER)
        ''')
        cursor.execute('''
        CREATE TABLE user_preferences(id INTEGER PRIMARY KEY, wakeup_time_hour INTEGER, wakeup_time_minute INTEGER,
        utc_offset INTEGER)
        ''')

        # Fill tables with initial data
        cursor.execute('''
        INSERT INTO server_settings(address, port) VALUES(?, ?)
        ''', ("", 49500))

        db.commit()


if __name__ == '__main__':
    main()
