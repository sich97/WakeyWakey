"""
File: client.py

This program lets you change settings as well as shut the alarm off once it's started.
"""

import configparser
import socket
import random

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
        management()


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
    # Create an INET streaming socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect((server_address, int(server_port)))

    # Request changing alarm state
    command = "set_alarm_state " + str(new_alarm_state)
    s.send(bytes(command, "utf-8"))

    # Close connection
    s.close()


def management():
    """
    Let's the user change settings on the server such as wakeup time, UTC offset, and more.
    :return: None
    """

    # Not yet defined
    print("Management not yet defined.")
    pass


if __name__ == '__main__':
    main()
