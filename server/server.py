"""
File: server.py

This program receives settings from the client (including wakeup time).
It also starts the alarm on the given wakeup time, and waits for an awoke signal from the client before stopping it.
"""

import sqlite3
import socket
import arrow
from multiprocessing import Process
import time

DATABASE_PATH = "server/db"
MAIN_LOOP_DELAY = 5
WAKEUP_WINDOW = 30


def main():
    # Initialization
    initialize()

    while True:
        # 5 second delay for safety
        time.sleep(MAIN_LOOP_DELAY)

        # Check if within wakeup window
        time_left = distance_from_wakeup_time()
        if time_left <= WAKEUP_WINDOW:
            # Go into alarm mode
            alarm_mode(time_left)


def alarm_mode(countdown):
    # Wait until actual wakeup time
    time.sleep(countdown * 60)

    # Do stuff


def distance_from_wakeup_time():
    """
    Returns how many minutes are left untill wakeup time
    :return: difference (int)
    """
    # Get newest settings
    wakeup_time_hour, wakeup_time_minute, utc_offset = load_settings("minimal")
    # Then convert to minutes
    wakeup_timestamp = convert_to_minutes(wakeup_time_hour, wakeup_time_minute)

    # Get current hour and minute
    current_time = get_local_time(utc_offset)
    current_time_parsed = current_time.split(":")
    current_hour = current_time_parsed[0]
    current_minute = current_time_parsed[1]
    # Then convert to minutes
    current_timestamp = convert_to_minutes(current_hour, current_minute)

    return wakeup_timestamp - current_timestamp


def convert_to_minutes(hour, minutes):
    """
    Takes any amount of hours, converts it to minutes and then adds the additional minutes
    :param hour: 60 minutes
    :type hour: int
    :param minutes: 60 seconds
    :type: int
    :return: timestamp (int)
    """
    hours_in_minutes = 60 * hour
    timestamp = hours_in_minutes + minutes

    return timestamp


def initialize():
    """
    Instantiates variables and loads settings
    :return: None
    """
    # Load settings
    bind_address, bind_port, wakeup_time_hour, wakeup_time_minute, utc_offset = load_settings("all")

    # Create server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((bind_address, bind_port))

    # Start the management process for communication with client
    management_process = Process(target=management, args=(s,))
    management_process.start()


def load_settings(degree):
    """
    Loads settings from the database
    :return: server_address (str), server_port (int), wakeup_time_hour (int), wakeup_time_minute (int),
    utc_offset (int)
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Get server settings
    sql_query = """SELECT address, port FROM server_settings"""
    cursor.execute(sql_query)
    row0 = cursor.fetchone()
    server_address = row0[0]
    server_port = row0[1]

    # Get user preferences
    sql_query = """SELECT wakeup_time_hour, wakeup_time_minute, utc_offset FROM user_preferences"""
    cursor.execute(sql_query)
    row0 = cursor.fetchone()
    wakeup_time_hour = row0[0]
    wakeup_time_minute = row0[1]
    utc_offset = row0[2]

    # Close database connection
    db.close()

    # Return information
    if degree == "minimal":
        return wakeup_time_hour, wakeup_time_minute, utc_offset
    else:
        return server_address, server_port, wakeup_time_hour, wakeup_time_minute, utc_offset


def management(s):
    """
    Listens for commands from the client and executes them
    :param s: The TCP socket
    :type s: socket.socket
    :return:
    """
    # Start listening for connections
    s.listen(5)
    while True:
        client_socket, client_address = s.accept()
        print(f"Connection from {client_address} has been established!")
        msg = client_socket.recv(1024)
        msg_decoded = msg.decode("utf-8")

        # Alarm state requested
        if msg_decoded == "get_alarm_state":
            # Verbose
            print(f"{client_address} requested the alarm state")
            alarm_state = get_alarm_state()
            client_socket.send(bytes(str(alarm_state), "utf-8"))
            client_socket.close()

        # Change alarm state requested
        elif "set_alarm_state" in msg_decoded:
            # No more need for the socket
            client_socket.close()

            # Get new requested alarm state
            parsed_string = msg_decoded.split(" ")
            new_alarm_state = int(parsed_string[1])

            # Verbose
            print(f"{client_address} requests alarm state to be {new_alarm_state}")

            # Set new alarm state
            set_alarm_state(new_alarm_state)


def get_alarm_state():
    """
    Returns the alarm state, which is stored in the database
    :return:
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Get alarm state
    sql_query = """SELECT alarm_state FROM server_settings"""
    cursor.execute(sql_query)
    row0 = cursor.fetchone()
    alarm_state = row0[0]

    # Close database connection
    db.close()

    return alarm_state


def set_alarm_state(new_alarm_state):
    """

    :param new_alarm_state: The new alarm state
    :type new_alarm_state: int
    :return:
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Set alarm state
    sql_query = """Update server_settings set alarm_state = ? where id = ?"""
    data = new_alarm_state, 1
    cursor.execute(sql_query, data)
    db.commit()

    # Close database connection
    db.close()


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
