"""
File: server.py

This program receives settings from the client (including wakeup time).
It also starts the alarm on the given wakeup time, and waits for an awoke signal from the client before stopping it.
"""

import sqlite3
import socket
import arrow

DATABASE_PATH = "server/db"


def main():
    # Initialization
    wakeup_time_hour, wakeup_time_minute, utc_offset, s = initialize()

    # Check if alarm should be on or not initially
    local_time = get_local_time(utc_offset)


def initialize():
    """
    Instantiates variables and loads settings
    :return: wakeup_time_hour (int), wakeup_time_minute (int), utc_offset (str), s (socket.socket)
    """
    # Load settings
    bind_address, bind_port, wakeup_time_hour, wakeup_time_minute, utc_offset = load_settings()

    # Create server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((bind_address, bind_port))

    return wakeup_time_hour, wakeup_time_minute, utc_offset, s


def load_settings():
    """
    Loads settings from the database
    :return: server_address (str), server_port (int), wakeup_time_hour (int), wakeup_time_minute (int), utc_offset (int)
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Get server settings
    cursor.execute('''
    SELECT address, port FROM server_settings
    ''')
    row0 = cursor.fetchone()
    server_address = row0[0]
    server_port = row0[1]

    # Get user preferences
    cursor.execute('''
    SELECT wakeup_time_hour, wakeup_time_minute, utc_offset FROM user_preferences
    ''')
    row0 = cursor.fetchone()
    wakeup_time_hour = row0[0]
    wakeup_time_minute = row0[1]
    utc_offset = row0[2]

    # Return information
    return server_address, server_port, wakeup_time_hour, wakeup_time_minute, utc_offset


def get_local_time(utc_offset):
    """
    Returns the global UTC as well as the offset UTC
    :param utc_offset: The amount of hours ahead of UTC
    :type utc_offset: int
    :return: utc (
    """
    utc = arrow.utcnow()
    local_time = utc.shift(hours=utc_offset)

    local_time_parsed = local_time.format("HH:mm")

    return local_time_parsed


if __name__ == '__main__':
    main()
