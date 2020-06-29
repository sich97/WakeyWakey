"""
File: client.py

This program let you manage the server settings (including wakeup time) as well as shut the alarm off once it's started.
"""

import configparser
import socket


def main():
    server_address, server_port, alarm_state = initialize()

    # If the server is in alarm mode
    if alarm_state == 1:

        # While having not completed the awoke_test properly
        awoke = False
        while not awoke:

            # Test whether the user is awoke or not
            awoke = awoke_test()

        # After having completed the awoke_test properly, stop the alarm
        set_alarm_state(server_address, server_port, 0)

    # If the server is not in alarm mode
    elif alarm_state == 0:
        set_alarm_state(server_address, server_port, 1)
        management()


def initialize():
    """
    Instantiates objects, variables, etc.
    Also connects to the server.
    :return: alarm_state (bool)
    """

    # Load settings
    server_address, server_port = load_settings()

    # Get server state
    alarm_state = get_alarm_state(server_address, server_port)

    return server_address, server_port, alarm_state


def load_settings():
    """
    Loads settings.ini and returns its information
    :return:
    """
    # Load settings.ini
    config = configparser.ConfigParser()
    config.read('client/settings.ini')
    config.sections()

    # Extract information
    server_address = config['SERVER']['Address']
    server_port = config['SERVER']['Port']

    # Return information
    return server_address, server_port


def get_alarm_state(server_address, server_port):
    """
    Returns a 1 if the server is in alarm mode, returns 0 otherwise
    :param server_address: The IP address of the server
    :type server_address: str
    :param server_port: The port number of the server
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

    # Verbose
    print("Alarm state is: " + str(alarm_state))

    # Close connection
    s.close()

    return alarm_state


def set_alarm_state(server_address, server_port, new_alarm_state):
    # Create an INET streaming socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect((server_address, int(server_port)))

    # Request changing alarm state
    command = "set_alarm_state " + str(new_alarm_state)
    s.send(bytes(command, "utf-8"))

    # Close connection
    s.close()


def awoke_test():
    print("Awoke test not yet defined")
    pass


def management():
    print("Management not yet defined")
    pass


if __name__ == '__main__':
    main()
