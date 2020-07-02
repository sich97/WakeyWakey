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
SECONDS_IN_A_DAY = 86400
MAIN_LOOP_DELAY_SECONDS = 5


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
            seconds_left = seconds_until_wakeup_time()
            print(f"Time until wakeup: {readable_time(seconds_left)}.")

            # If within wakeup window
            if seconds_left <= get_wakeup_window() * 60:
                print("Entered wakeup window.")
                # Go into alarm mode
                alarm_mode(seconds_left)


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
        # Accept any connection
        client_socket, client_address = s.accept()
        print(f"Connection from {client_address} has been established!")

        # Receive message and decode it
        msg = client_socket.recv(1024)
        command = msg.decode("utf-8").split(" ")

        # Alarm state requested
        if command[0] == "get_alarm_state":
            # Verbose
            print(f"{client_address} requested the alarm state.")

            # Get the alarm state
            alarm_state = get_alarm_state()

            # Reply with the alarm state
            client_socket.send(bytes(str(alarm_state), "utf-8"))

        # Change alarm state requested
        elif command[0] == "set_alarm_state":
            # Verbose
            print(f"{client_address} requests alarm state to be {command[1]}.")

            # Set new alarm state
            set_alarm_state(int(command[1]))

        # Set active state
        elif command[0] == "set_active_state":
            # Verbose
            print(f"{client_address} requests active state to be {command[1]}.")

            # Set new active_state
            set_active_state(int(command[1]))

        elif command[0] == "set_wakeup_hour":
            # Verbose
            print(f"{client_address} requests wakeup hour to be {command[1]}.")

            # Set new wakeup hour
            set_wakeup_hour(int(command[1]))

        elif command[0] == "set_wakeup_minute":
            # Verbose
            print(f"{client_address} requests wakeup minute to be {command[1]}.")

            # Set new wakeup hour
            set_wakeup_minute(int(command[1]))

        elif command[0] == "set_wakeup_window":
            # Verbose
            print(f"{client_address} requests wakeup window to be {command[1]}.")

            # Set new wakeup window
            set_wakeup_window(int(command[1]))

        elif command[0] == "set_utc_offset":
            # Verbose
            print(f"{client_address} requests UTC offset to be {command[1]}.")

            # Set new wakeup window
            set_utc_offset(int(command[1]))

        elif command[0] == "get_user_preferences":
            # Verbose
            print(f"{client_address} requested user_preferences.")

            # Get the user preferences
            user_preferences = get_user_preferences()

            # Reply with the user preferences
            client_socket.send(bytes(str(user_preferences), "utf-8"))

        # Close the socket
        client_socket.close()


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


def set_wakeup_hour(new_wakeup_hour):
    """
    Sets the wakeup hour to the parameter new_wakeup_hour.
    :param new_wakeup_hour: The new wakeup hour.
    :type new_wakeup_hour: int
    :return: None
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Set active state
    sql_query = """Update user_preferences set wakeup_time_hour = ? where id = ?"""
    data = new_wakeup_hour, 1
    cursor.execute(sql_query, data)
    db.commit()

    # Close database connection
    db.close()


def set_wakeup_minute(new_wakeup_minute):
    """
    Sets the wakeup minute to the parameter new_wakeup_minute.
    :param new_wakeup_minute: The new wakeup minute.
    :type new_wakeup_minute: int
    :return: None
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Set active state
    sql_query = """Update user_preferences set wakeup_time_minute = ? where id = ?"""
    data = new_wakeup_minute, 1
    cursor.execute(sql_query, data)
    db.commit()

    # Close database connection
    db.close()


def get_wakeup_window():
    """
    Returns the wakeup window, which is stored in the database.
    :return: wakeup_window (int)
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Get wakeup window
    sql_query = """SELECT wakeup_window FROM user_preferences"""
    cursor.execute(sql_query)
    row0 = cursor.fetchone()
    wakeup_window = row0[0]

    # Close database connection
    db.close()

    return wakeup_window


def set_wakeup_window(new_wakeup_window):
    """
    Sets the wakeup window to the parameter new_wakeup_window.
    :param new_wakeup_window: The new wakeup window in minutes.
    :type new_wakeup_window: int
    :return: None
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Set active state
    sql_query = """Update user_preferences set wakeup_window = ? where id = ?"""
    data = new_wakeup_window, 1
    cursor.execute(sql_query, data)
    db.commit()

    # Close database connection
    db.close()


def set_utc_offset(new_utc_offset):
    """
    Sets the UTC offset to the parameter new_utc_offset.
    :param new_utc_offset: The new UTC offset.
    :type new_utc_offset: int
    :return: None
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Set utc offset
    sql_query = """Update user_preferences set utc_offset = ? where id = ?"""
    data = new_utc_offset, 1
    cursor.execute(sql_query, data)
    db.commit()

    # Close database connection
    db.close()


def get_user_preferences():
    """
    Starts by grabbing the SQL for the user_preferences table from the sqlite_master table.
    Then parses it in order to extract only the column names, excluding the column named 'id'.
    Then grabs the values of the first row in the user_preferences table
    for each column except for the column named 'id'.
    Combines these two lists into a dictionary and returns said dictionary.
    :return: user_preferences (dict)
    """
    # Instantiate database connection
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Get user preferences column names
    sql_query = """SELECT sql from sqlite_master where tbl_name = 'user_preferences'"""
    cursor.execute(sql_query)
    user_preferences_sql = cursor.fetchone()
    user_preferences_sql_parsed = str(user_preferences_sql[0]).replace("\n    ", " ")
    user_preferences_sql_parsed = user_preferences_sql_parsed.split(", ")
    del user_preferences_sql_parsed[0]
    user_preferences_column_names = []
    for i in range(len(user_preferences_sql_parsed)):
        column_name = user_preferences_sql_parsed[i].split(" ")[0]
        user_preferences_column_names.append(column_name)

    # Get user preferences values
    sql_query = """SELECT * FROM user_preferences where id = 1"""
    cursor.execute(sql_query)
    user_preferences_values = cursor.fetchone()
    user_preferences_values_list = list(user_preferences_values)
    del user_preferences_values_list[0]

    # Close database connection
    db.close()

    # Convert to dictionary
    user_preferences = dict(zip(user_preferences_column_names, user_preferences_values_list))

    return user_preferences


"""
########################################################################################################################
                                                        TIME MANAGEMENT
########################################################################################################################
"""


def readable_time(seconds):
    """
    Takes any number of seconds and turns it into days, hours, minutes and seconds in a readable format.
    :param seconds: 1/60th of a minute
    :type seconds: int
    :return: output (str)
    """
    # Convert to days
    days, hours, minutes, seconds = seconds_to_days(seconds)

    # Instantiate output_string
    output = ""

    # Add if non-zero
    if days != 0:
        output += str(days) + " days, "
    if hours != 0:
        output += str(hours) + " hours, "
    if minutes != 0:
        output += str(minutes) + " minutes, "
    if seconds != 0:
        output += str(seconds) + " seconds"

    return output


def seconds_to_days(seconds):
    """
    Takes any number of seconds and returns its constitutive amount of days, hours, minutes and remaining seconds.
    :param seconds: 1/60th of a minute.
    :type seconds: int
    :return: days (int), remainder_hours (int), minutes (int), seconds (int)
    """
    minutes, seconds = seconds_to_minutes(seconds)
    hours, minutes, seconds = seconds_to_hours(convert_to_seconds(0, 0, minutes, seconds))
    days = hours // 24
    remainder_hours = hours % 24

    return days, remainder_hours, minutes, seconds


def seconds_to_hours(seconds):
    """
    Takes any number of seconds and returns its constitutive amount of hours, minutes and remaining seconds.
    :param seconds: 1/60th of a minute.
    :type seconds: int
    :return: hours (int), remainder_minutes (int), seconds (int)
    """
    minutes, seconds = seconds_to_minutes(seconds)
    hours = minutes // 60
    remainder_minutes = minutes % 60

    return hours, remainder_minutes, seconds


def seconds_to_minutes(seconds):
    """
    Takes any number of seconds and returns its constitutive amount ot minutes and remaining seconds.
    :param seconds: 1/60th of a minute.
    :type seconds: int
    :return: minutes (int), remainder_seconds (int)
    """
    minutes = seconds // 60
    remainder_seconds = seconds % 60

    return minutes, remainder_seconds


def seconds_until_wakeup_time():
    """
    Returns how many seconds are left until wakeup time.
    :return: time_left (int)
    """
    # Get newest settings
    wakeup_time_hour, wakeup_time_minute, utc_offset = load_settings("minimal")

    # Then get the wakeup timestamp
    wakeup_timestamp_in_seconds = convert_to_seconds(0, wakeup_time_hour, wakeup_time_minute, 0)

    # Time left until wakeup time
    seconds_left = wakeup_timestamp_in_seconds - current_time_in_seconds(utc_offset)

    # In the case that time_left is negative (meaning that the alarm has already gone off this day)
    if seconds_left < 0:
        # Add a day
        seconds_left += SECONDS_IN_A_DAY

    return seconds_left


def current_time_in_seconds(utc_offset):
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
    current_second = int(current_time_parsed[2])

    # Then get the total amount of seconds
    current_timestamp = convert_to_seconds(0, current_hour, current_minute, current_second)

    return current_timestamp


def convert_to_seconds(days, hour, minutes, seconds):
    """
    Takes any amount of days, hours, minutes and seconds and returns the total amount of seconds.
    :param days: 24 hours.
    :type days: int
    :param hour: 60 minutes.
    :type hour: int
    :param minutes: 60 seconds.
    :type: int
    :param seconds: 1/60th of a minute
    :type seconds: int
    :return: timestamp (int)
    """

    return ((days * 24 + hour) * 60 + minutes) * 60 + seconds


def get_local_time(utc_offset):
    """
    Gets the current UTC time, shifts it according to the parameter utc_offset, then returns it in the format HH:mm:ss.
    :param utc_offset: The amount of hours ahead of UTC.
    :type utc_offset: int
    :return: local_time_parsed (arrow)
    """
    # get the current UTC time
    utc = arrow.utcnow()

    # Apply UTC offset
    local_time = utc.shift(hours=utc_offset)

    # Format it
    local_time_parsed = local_time.format("HH:mm:ss")

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
    print("Waiting for " + str(countdown) + " seconds...")
    time.sleep(countdown)

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
    set_alarm_state(0)
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
