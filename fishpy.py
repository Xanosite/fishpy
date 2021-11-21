'''
Welcome to FishPy
This was made to interact with the Fishbowl API
'''
import base64
import hashlib
import json
import os
import socket
import struct
import sys

# Primary class for the api communication
class connection:
    # Initialization, get required app data
    def __init__(
            self, app_data_location = "/data/application-data.dat",
            status_codes_location = "/data/status-codes.dat"):
        self.cwd = os.getcwd()
        application_data = {}
        # Try to read the application data from file as JSON
        try:
            application_data = json.loads(open(self.cwd + app_data_location, "r").read())
        # Terminate if file cannot be found at address
        except OSError as e:
            print(f"Exception: Application data file not found.")
            print(f"OSError: {e}")
            sys.exit(1)
        # Terminate if the application-data.dat file cannot be parsed as json
        except json.JSONDecodeError as e:
            print(f"Exception: Application data file could not be parsed as a json file.")
            print(f"json.JSONDecodeError: {e.msg}")
            print(f"See read-me-usage.txt in \"{self.cwd}/documentation\" for more information.")
            sys.exit(1)
        # Try to get the status codes dictionary
        try:
            self.status_codes_dict = json.loads(open(self.cwd + status_codes_location, "r").read())
        # Terminate if file cannot be found at address
        except OSError as e:
            print(f"Exception: Status codes file not found.")
            print(f"OSError: {e}")
            sys.exit(1)
        # Terminate if the application-data.dat file cannot be parsed as json
        except json.JSONDecodeError as e:
            print(f"Exception: Status codes file could not be parsed as a json file.")
            print(f"json.JSONDecodeError: {e.msg}")
            print(f"See read-me-usage.txt in \"{self.cwd}/documentation\" for more information.")
            sys.exit(1)
        # Try to get the required information from application-data.dat
        try:
            self.application_identification = application_data["IAID"]
            self.application_description = application_data["IADescription"]
            self.application_name = application_data["IAName"]
            self.fishbowl_host = application_data["Host"]
            self.fishbowl_port = int(application_data["Port"])
        # Terminate is dictionary does not contain required values
        except KeyError as e:
            print("Exception: application-data.dat is not formatted correctly.")
            print(f"See read-me-usage.txt in \"{self.cwd}/documentation\" for more information.")
            print(e)
            sys.exit(1)
        # Try to make a connection with the fishbowl server
        try:
            self.fishbowl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.fishbowl_socket.connect((self.fishbowl_host, self.fishbowl_port))
        # Terminate on failure to connect
        except TimeoutError:
            print("Exception: Connection timed out.")
            print("Connection could not be established with the fishbowl server.")
            sys.exit(1)
        except InterruptedError:
            print("Exception: Connection interrupted.")
            print("Connection could not be established with the fishbowl server.")
            sys.exit(1)
    # Send data to fishbowl server
    def __fishbowl_connection_communicate(self, data):
        # Convert data to message and send
        serialized_message= json.dumps(data).encode()
        message_length = struct.pack('>L', len(serialized_message))
        outbound_message = message_length + serialized_message
        self.fishbowl_socket.sendall(outbound_message)
        # Get reply from server
        byte_count = 0
        inbound_message = bytearray()
        inbound_message_length = struct.unpack('>L', self.fishbowl_socket.recv(4))[0]
        while byte_count < inbound_message_length:
            inbound_message.append(ord(self.fishbowl_socket.recv(1)))
            byte_count += 1
        return inbound_message.decode('latin-1')
    # Packages messages into FbiMsgsRq format
    def __fishbowl_msgs_rs(self, message):
        return  {
                    "FbiJson":{
                        "Ticket":{
                            "Key":self.key
                            },
                        "FbiMsgsRq":message
                    }
                }
    # Gets status code descriptions
    def __fishbowl_status_code(self, code):
        description = ""
        try:
            description = self.status_codes_dict[str(code)]
        except KeyError as e:
            print("Exception: Server responded with an unknown status code")
            print(e)
            sys.exit(1)
        return description
    # Login to fishbowl server and get key, status
    def login(self, username, password):
        # Format password for fishbowl server
        hidden_password = base64.b64encode(hashlib.md5(password.encode()).digest()).decode()
        self.key = ""
        login_dict =    self.__fishbowl_msgs_rs({
                            "LoginRq":{
                                "IAID":self.application_identification,
                                "IADescription":self.application_description,
                                "UserName":username,
                                "IAName":self.application_name,
                                "UserPassword":hidden_password
                            }
                        })
        # Send login request to server, get response
        server_response =  self.__fishbowl_connection_communicate(login_dict)
        # Try to parse as JSON
        try:
            server_response = json.loads(server_response)
        except json.JSONDecodeError as e:
            print("Exception: Fishbowl server response could not be proccessed as JSON")
            print(e)
            sys.exit(1)
        # Try to retreive status code and key
        status_code = ""
        try:
            self.key = server_response["FbiJson"]["Ticket"]["Key"]
            status_code = server_response["FbiJson"]["FbiMsgsRs"]["statusCode"]
        except KeyError as e:
            print("Exception: Fishbowl server reponse did not contain expected JSON")
            print(e)
            sys.exit(1)
        status = self.__fishbowl_status_code(status_code)
        return (status_code, status)
    # Logout of fishbowl server
    def logout(self):
        logout_dict =   self.__fishbowl_msgs_rs({"LogoutRq":""})
        server_response = self.__fishbowl_connection_communicate(logout_dict)
        # Try to retreive status code
        status_code = ""
        try:
            status_code = json.loads(server_response)["FbiJson"]["FbiMsgsRs"]["statusCode"]
        except json.JSONDecodeError as e:
            print("Exception: Fishbowl server response was not JSON")
            print(e)
            sys.exit(1)
        except KeyError as e:
            print("Exception: Fishbowl server reponse did not contain expected JSON")
            print(e)
            sys.exit(1)
        status = self.__fishbowl_status_code(status_code)
        return (status_code, status)
    # Executes basic queries against the server
    def simple_query(self, query):
        # Fromat query to be sent to fishbowl
        query_dict = {"ExecuteQueryRq":{"Query":query}}
        message_dict = self.__fishbowl_msgs_rs(query_dict)
        try:
            server_response = json.loads(self.__fishbowl_connection_communicate(message_dict))
        except json.JSONDecodeError as e:
            print("Exception: Server response was not in JSON format.")
            print(e)
            sys.exit(1)
        status_code = server_response["FbiJson"]["FbiMsgsRs"]["statusCode"]
        status = (status_code, self.__fishbowl_status_code(status_code))
        if status_code == 1000:
            query_response = server_response["FbiJson"]["FbiMsgsRs"]["ExecuteQueryRs"]["Rows"]["Row"]
        return (status, query_response)
