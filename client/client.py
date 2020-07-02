"""
File: client.py

This program lets you change settings as well as shut the alarm off once it's started.
"""

import configparser
import socket
import random
import ast
import platform
import os

SETTINGS_PATH = "client/settings.ini"


def main():
    """
    After initialization, the program branches into two cases; One in which the alarm is on and you'll be able to
    turn it off by succeeding the awake test. And another in which the alarm is off and you'll be able to change
    settings, such as wakeup time, UTC offset, and more.
    :return: None
    """
    # Initialization
    server_address, server_port, alarm_state = initialize()

    # If the alarm is on
    if alarm_state == 1:

        # Test if the user is awake
        awake_test()

        # After having completed the awoke_test properly, stop the alarm
        set_alarm_state(server_address, server_port, 0)

    # If the server is not in alarm mode
    elif alarm_state == 0:

        # Go into management mode
        management(server_address, server_port)


"""
########################################################################################################################
                                                        INITIALIZATION
########################################################################################################################
"""


def initialize():
    """
    Loads settings from settings.ini and gets the current state of the alarm.
    :return: server_address (str), server_port(int), alarm_state (int)
    """
    # Load settings from settings.ini
    server_address, server_port = load_settings()

    # Get server state
    alarm_state = get_alarm_state(server_address, server_port)

    return server_address, server_port, alarm_state


def load_settings():
    """
    Loads settings.ini and returns its information.
    :return: server_address (str), server_port (str)
    """
    # Load settings.ini
    config = configparser.ConfigParser()
    config.read(SETTINGS_PATH)
    config.sections()
    server_address = config['SERVER']['Address']
    server_port = config['SERVER']['Port']

    return server_address, server_port


def get_alarm_state(server_address, server_port):
    """
    Returns the value of alarm_state, which is stored in the database on the server.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :return: server_state (int)
    """
    # Create an INET streaming socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect((server_address, int(server_port)))

    # Request alarm state
    command = "get_alarm_state"
    s.send(bytes(command, "utf-8"))

    # Receive and decode response
    msg = s.recv(1024)
    msg_decoded = msg.decode("utf-8")
    alarm_state = int(msg_decoded)

    # Close connection
    s.close()

    return alarm_state


"""
########################################################################################################################
                                                        AWAKE TEST
########################################################################################################################
"""


def awake_test():
    """
    Gives the user challenges until one is overcome, in which case we assume the user is awake enough to not fall back
    to sleep.
    :return: None
    """
    awake = False
    while not awake:

        # Temporary challenge for development purposes
        first_int = random.randint(1, 10)
        second_int = random.randint(1, 10)
        print("What is " + str(first_int) + " + " + str(second_int) + "?")
        answer = int(input("Type your answer here: "))
        if answer == first_int + second_int:
            awake = True
            print("Congratulations, you're awake!")
        else:
            print("You're not yet awake enough. Try again.")


"""
########################################################################################################################
                                                        MANAGEMENT
########################################################################################################################
"""


def server_connection(server_address, server_port):
    """
    Creates a server connection and returns the socket
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :return: s (socket.socket)
    """
    # Create an INET streaming socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect((server_address, int(server_port)))

    # Return the socket
    return s


def set_alarm_state(server_address, server_port, new_alarm_state):
    """
    Sets the value of alarm_state, which is stored in the database on the server.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :param new_alarm_state: The requested new value of alarm_state.
    :type new_alarm_state: int
    :return: None
    """
    # Connect to server
    connection = server_connection(server_address, server_port)

    # Request changing alarm state
    command = "set_alarm_state " + str(new_alarm_state)
    connection.send(bytes(command, "utf-8"))

    # Close connection
    connection.close()


def management(server_address, server_port):
    """
    Shows the current user preferences stored on server.
    Then lets the user change them.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :return: None
    """
    system = platform.system()
    not_done = True

    # While the user is not done changing settings
    while not_done:
        # Clear the console
        if system == "Windows":
            os.system("cls")
        else:
            os.system("clear")

        # Display current preferences
        user_preferences = load_user_preferences(server_address, server_port)
        display_user_preferences(user_preferences)

        # Changing preferences
        print("\nInput the number of the setting you wish to change: ", end="")
        preference_to_change = int(input())

        # If changing active_state
        if preference_to_change == 1:
            current_active_state = user_preferences["active_state"]
            change_active_state(server_address, server_port, current_active_state)

        # If changing wakeup time
        if preference_to_change == 2:
            print("Changing wakeup time.")
            new_wakeup_hour = int(input("Please input hour: "))
            new_wakeup_minute = int(input("Please input minute: "))

            change_wakeup_time(server_address, server_port, "hour", new_wakeup_hour)
            change_wakeup_time(server_address, server_port, "minute", new_wakeup_minute)


def change_wakeup_time(server_address, server_port, hour_or_minute, value):
    """
    Changes the given type (hours or minute) to whatever value.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :param hour_or_minute: Either 'hour' or 'minute'.
    :type hour_or_minute: str
    :param value: The new value for the given type.
    :type value: int
    :return: None
    """
    # Connect to server
    connection = server_connection(server_address, server_port)

    # Request changing alarm state
    command = "set_wakeup_" + hour_or_minute + " " + str(value)
    connection.send(bytes(command, "utf-8"))

    # Close connection
    connection.close()


def change_active_state(server_address, server_port, current_active_state):
    """
    Changes the active state to whatever it wasn't before.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :param current_active_state: What the active state was before calling this function.
    :type current_active_state: int
    :return: None
    """
    if current_active_state == 0:
        set_active_state(server_address, server_port, 1)
    else:
        set_active_state(server_address, server_port, 0)


def set_active_state(server_address, server_port, new_active_state):
    """
    Sends a command to the server requesting the active state to be change to the new_active_state parameter.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :param new_active_state: The new active state.
    :type new_active_state: int
    :return: None
    """
    # Connect to server
    connection = server_connection(server_address, server_port)

    # Request changing alarm state
    command = "set_active_state " + str(new_active_state)
    connection.send(bytes(command, "utf-8"))

    # Close connection
    connection.close()


def display_user_preferences(user_preferences):
    """
    Shows the current user preferences.
    :param user_preferences: The current user preferences.
    :type user_preferences: dict
    :return: None
    """
    print("These are your current preferences stored on the server:")
    print("1.\tActive:\t\t", end="")
    if user_preferences["active_state"] == 1:
        print("Yes")
    else:
        print("No")
    print("2.\tWakeup time:\t" + str(user_preferences["wakeup_time_hour"]) + ":", end="")
    if user_preferences["wakeup_time_minute"] < 10:
        print("0", end="")
    print(str(user_preferences["wakeup_time_minute"]))
    print("3.\tUTC offset:\t+" + str(user_preferences["utc_offset"]))


def load_user_preferences(server_address, server_port):
    """
    Gets the user preferences as a dictionary from the server.
    :param server_address: The IP address of the server.
    :type server_address: str
    :param server_port: The port number of the server.
    :type server_port: str
    :return: user_preferences (dict)
    """
    # Connect to server
    connection = server_connection(server_address, server_port)

    # Request user preferences
    command = "get_user_preferences"
    connection.send(bytes(command, "utf-8"))

    # Receive and decode response
    msg = connection.recv(1024)
    user_preferences = msg.decode("utf-8")

    # Close connection
    connection.close()

    # Convert to dictionary
    user_preferences = ast.literal_eval(user_preferences)

    return user_preferences


if __name__ == '__main__':
    main()
