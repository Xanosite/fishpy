'''
functions for managing connections with external data
'''
import sys;
import socket
import struct
import json
import api

# Create a socket connection to fishbowl server
def fishbowl_connection_create(primary_directory, app_data_name):
    host = None
    port = None
    app_data_dict = {}
    # try to get host information
    try:
        app_data_dict = json.loads(open(app_data_name, "r").read())
    except (FileNotFoundError, OSError):
        # report error to user and begin termination of program sequence
        return api.dat_missing_incorrect(primary_directory, app_data_name)
    try:
        host = app_data_dict["Host"]
        port = int(app_data_dict["Port"])
    except (KeyError):
        return api.dat_missing_incorrect(primary_directory, app_data_name)
    # create socket
    socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # attempt connection
    try:
        socket_connection.connect((host, port))
    except OSError:
        print("A connection to the fishbowl server could not be made.")
        print("Please check network connections and server address.")
        return 1
    return socket_connection

# send the packet to fishbowl and receive reply
def fishbowl_connection_communicate(data_dict, primary_directory,
                                    app_data_name):
    byte_count = 0
    inbound_packet = bytearray()
    #connect to server
    socket_connection = fishbowl_connection_create(primary_directory, app_data_name)
    if socket_connection == 1: return 1
    # convert dict to a json formatted string && get length
    serial_data = json.dumps(data_dict).encode()
    packet_length = struct.pack('>L', len(serial_data))
    # create data packet
    outbound_packet = packet_length + serial_data
    # try to send the packet
    try:
        socket_connection.sendall(outbound_packet)
    except OSError:
        print("Message could not be sennt to the fishbowl server.")
        print("Please check network connections and server address.")
        socket_connection.close()
        return 1
    # try to read the response from the server
    try:
        # determine size of inbound packet
        inbound_packet_length_packed = socket_connection.recv(4)
        inbound_packet_length = struct.unpack('>L', inbound_packet_length_packed)[0]
        # retreive data from packet
        while byte_count < inbound_packet_length:
            inbound_packet.append(ord(socket_connection.recv(1)))
            byte_count += 1
    except TimeoutError:
        print("Connection to fishbowl server timed out")
        socket_connection.close()
        return 1
    except OSError:
        print("An error occurred while receiving the response form the server")
        socket_connection.close()
        return 1
    socket_connection.close()
    return inbound_packet.decode('latin-1')
