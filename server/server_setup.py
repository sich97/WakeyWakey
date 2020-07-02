"""
File: server_setup.py

This file creates / or resets the server database.
"""

import sqlite3
import os

DATABASE_PATH = "server/db"


def main():
    """
    In the case that a database already exists, ask the user if it's really okay to reset it. If no, then do nothing
    and exit. If yes, delete the existing database and create a new one.
    :return: None
    """
    reset = False

    # A database already exists
    if os.path.isfile(DATABASE_PATH):
        # Ask the user what to do
        print("Database already exists. Do you want it reset? [NO]: ", end="")
        reset = input()

        # User answered yes
        if reset == "YES" or reset == "Yes" or reset == "yes":
            # Delete the database
            os.remove(DATABASE_PATH)

            # Create a new one
            create_database()

    # A database does not exist
    else:
        create_database()


def create_database():
    """
    Creates a database and fills it with initial information.
    :return: None
    """
    # Establish database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Create the server settings table
    sql_query = """CREATE TABLE server_settings(id INTEGER PRIMARY KEY, address TEXT, port INTEGER,
    alarm_state INTEGER)"""
    cursor.execute(sql_query)
    # Fill the table with data
    sql_query = """INSERT INTO server_settings(address, port, alarm_state) VALUES(?, ?, ?)"""
    data = "", 49500, 0
    cursor.execute(sql_query, data)

    # Create the user preferences table
    sql_query = """CREATE TABLE user_preferences(id INTEGER PRIMARY KEY, wakeup_time_hour INTEGER,
    wakeup_time_minute INTEGER, utc_offset INTEGER, wakeup_window INTEGER, active_state INTEGER)"""
    cursor.execute(sql_query)
    # Fill the table with data
    sql_query = """INSERT INTO user_preferences(wakeup_time_hour, wakeup_time_minute, utc_offset, wakeup_window,
    active_state)
    VALUES(?, ?, ?, ?, ?)"""
    data = 16, 00, 2, 5, 0
    cursor.execute(sql_query, data)

    # Save changes to database
    db.commit()

    # Close database
    db.close()


if __name__ == '__main__':
    main()
