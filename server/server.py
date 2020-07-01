"""
File: server.py

This program receives settings from the client (including wakeup time).
It also starts the alarm on the given wakeup time, and waits for an awake signal from the client before stopping it.
"""

import sqlite3
import multiprocessing
import socket
import arrow
import time

DATABASE_PATH = "server/db"
MAIN_LOOP_DELAY_SECONDS = 5
WAKEUP_WINDOW_MINUTES = 5
MINUTES_IN_A_DAY = 1440


def main():
    """
    After initializing, this function loops and checks if the current time is within the wakeup window.
    If it is, it goes into alarm mode, meaning any change to the wakeup time is futile as it starts counting down
    the remaining amount of seconds before it eventually sounds the alarm. In that case, the alarm continues until
    the alarm_state in the database is set to 0 (which can normally only be done by completing the awake_test
    through the client.
    :return: None
    """
    # Initialization
    initialize()

    # Main loop
    while True:
        # Loop delay
        time.sleep(MAIN_LOOP_DELAY_SECONDS)

        # If active
        if get_active_state():
            # Check if within wakeup window
            time_left = minutes_until_wakeup_time()
            print("Minutes until wakeup: " + str(time_left))

            # If within wakeup window
            if time_left <= WAKEUP_WINDOW_MINUTES:
                print("Entered wakeup window.")
                # Go into alarm mode
                alarm_mode(time_left)


"""
########################################################################################################################
                                                        INITIALIZATION
########################################################################################################################
"""


def initialize():
    """
    Loads settings and sets up TCP communication.
    :return: None
    """
    # Load settings
    bind_address, bind_port, wakeup_time_hour, wakeup_time_minute, utc_offset = load_settings("all")

    # Create server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((bind_address, bind_port))

    # Start the management process for communication with client
    management_process = multiprocessing.Process(target=communication, args=(s,))
    management_process.start()


def load_settings(degree):
    """
    Loads settings from the database.
    :param degree: Determines which settings to return.
    :type degree: str
    :return: depends on the degree
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


"""
########################################################################################################################
                                                        COMMUNICATION
########################################################################################################################
"""


def communication(s):
    """
    Listens for commands from the client and executes them.
    :param s: The TCP socket.
    :type s: socket.socket
    :return: None
    """
    # Listen for connections
    s.listen(5)
    while True:
        client_socket, client_address = s.accept()
        print(f"Connection from {client_address} has been established!")
        msg = client_socket.recv(1024)
        msg_decoded = msg.decode("utf-8")

        # Alarm state requested
        if msg_decoded == "get_alarm_state":
            # Verbose
            print(f"{client_address} requested the alarm state.")
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
            print(f"{client_address} requests alarm state to be {new_alarm_state}.")

            # Set new alarm state
            set_alarm_state(new_alarm_state)


def get_alarm_state():
    """
    Returns the alarm state, which is stored in the database.
    :return: alarm_state (int)
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
    Sets the alarm state, which is stored in the database, to the parameter new_alarm_state.
    :param new_alarm_state: The new alarm state.
    :type new_alarm_state: int
    :return: None
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


def get_active_state():
    """
    Returns the active state, which is stored in the database.
    :return: active_state (int)
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Get active state
    sql_query = """SELECT active_state FROM user_preferences"""
    cursor.execute(sql_query)
    row0 = cursor.fetchone()
    active_state = row0[0]

    # Close database connection
    db.close()

    return active_state


def set_active_state(new_active_state):
    """
    Sets the active state, which is stored in the database, to the parameter new_active_state.
    :param new_active_state: The new alarm state.
    :type new_active_state: int
    :return: None
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Set active state
    sql_query = """Update user_preferences set active_state = ? where id = ?"""
    data = new_active_state, 1
    cursor.execute(sql_query, data)
    db.commit()

    # Close database connection
    db.close()


"""
########################################################################################################################
                                                        TIME MANAGEMENT
########################################################################################################################
"""


def minutes_until_wakeup_time():
    """
    Returns how many minutes are left until wakeup time.
    :return: time_left (int)
    """
    # Get newest settings
    wakeup_time_hour, wakeup_time_minute, utc_offset = load_settings("minimal")

    # Then get the wakeup timestamp
    wakeup_timestamp = convert_to_minutes(wakeup_time_hour, wakeup_time_minute)

    # Get current timestamp
    current_timestamp = current_time_in_minutes(utc_offset)

    # Time left until wakeup time
    time_left = wakeup_timestamp - current_timestamp

    # In the case that time_left is negative (meaning that the alarm has already gone off this day)
    if time_left < 0:
        # Add a day
        time_left += MINUTES_IN_A_DAY

    return time_left


def current_time_in_minutes(utc_offset):
    """
    Gets the current hour and minute and returns the total of that in minutes.
    :param utc_offset: The amount of hours ahead of UTC.
    :type utc_offset: int
    :return: current_timestamp (int)
    """
    # Get the current time
    current_time = get_local_time(utc_offset)

    # Parse it into hours and minutes
    current_time_parsed = current_time.split(":")
    current_hour = int(current_time_parsed[0])
    current_minute = int(current_time_parsed[1])

    # Then get the total amount of minutes
    current_timestamp = convert_to_minutes(current_hour, current_minute)

    return current_timestamp


def convert_to_minutes(hour, minutes):
    """
    Takes any amount of hours, converts it to minutes and then adds the additional minutes.
    :param hour: 60 minutes.
    :type hour: int
    :param minutes: 60 seconds.
    :type: int
    :return: timestamp (int)
    """
    hours_in_minutes = 60 * hour
    timestamp = hours_in_minutes + minutes

    return timestamp


def get_local_time(utc_offset):
    """
    Gets the current UTC time, shifts it according to the parameter utc_offset, then returns it in the format HH:mm.
    :param utc_offset: The amount of hours ahead of UTC.
    :type utc_offset: int
    :return: local_time_parsed (arrow)
    """
    # get the current UTC time
    utc = arrow.utcnow()

    # Apply UTC offset
    local_time = utc.shift(hours=utc_offset)

    # Format it
    local_time_parsed = local_time.format("HH:mm")

    return local_time_parsed


"""
########################################################################################################################
                                                        ALARM
########################################################################################################################
"""


def alarm_mode(countdown):
    """
    Waits out the remaining amount of time until actual wakeup time, then sets the alarm_state in the database to 1.
    Then sounds the alarm while alarm_state in the database is still 1.
    :param countdown: The remaining time until actual wakeup time, in minutes.
    :type countdown: int
    :return: None
    """
    # Wait until actual wakeup time
    seconds_left = countdown * 60
    print("Waiting for " + str(seconds_left) + " seconds...")
    time.sleep(seconds_left)

    print("Actual wakeup time reached.")

    # Sound the alarm
    set_alarm_state(1)
    while get_alarm_state() == 1:
        print("Still not awake...")
        buzzer(1)
        time.sleep(1)
        buzzer(0)
        time.sleep(1)

    print("User is awake!")

    # Make sure the buzzer turns off
    buzzer(0)

    # Deactivate active_state
    set_active_state(0)


def buzzer(state):
    """
    Turns the buzzer either on or off.
    :param state: The requested new state of the buzzer (1 is on, 0 is off).
    :type state: int
    :return: None
    """
    if state == 1:
        print("Alarm goes BEEP!")
    else:
        print("Alarm goes silent.")


if __name__ == '__main__':
    main()
