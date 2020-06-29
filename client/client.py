"""
File: client.py

This program let you manage the server settings (including wakeup time) as well as shut the alarm off once it's started.
"""

import configparser
import socket


def main():
    server_state = initialize()

    # If the server is in alarm mode
    if server_state == 1:

        # While having not completed the awoke_test properly
        awoke = False
        while not awoke:

            # Test whether the user is awoke or not
            awoke = awoke_test()

        # After having completed the awoke_test properly, stop the alarm
        server_state = 0
        pass

    # If the server is not in alarm mode
    elif server_state == 0:
        management()


def initialize():
    """
    Instantiates objects, variables, etc.
    Also connects to the server.
    :return: server_state (int)
    """

    # Load settings
    server_address, server_port = load_settings()

    # Get server state
    server_state = get_server_state(server_address, server_port)

    return server_state


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


def get_server_state(server_address, server_port):
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



    return 0


if __name__ == '__main__':
    main()
