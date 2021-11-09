'''
Function wrapper file
Designed to contain commonly used functions
'''
import os
import sys
import struct
import json
import hashlib
import base64
from getpass import getpass
import streams

# create the login_dict to be sent to fishbowl via FbiJson:{FbiMsgsRq:{login_dict}}
def make_login_msg  (username, password, primary_directory,
                    app_data_name):
    key = ""
    login_dict = {}
    md5_pass = None
    b64_md5_pass = None
    app_data_dict = {}
    # formats password to fishbowl specification: base64(md5(password))
    md5_pass = hashlib.md5(password.encode()).digest()
    b64_md5_pass = base64.b64encode(md5_pass).decode()
    # retreive specific client data from file, parses from json into dict
    try:
        app_data_dict = json.loads(open(app_data_name, "r").read())
    except (FileNotFoundError, OSError):
        # report error to user and begin termination of program sequence
        return dat_missing_incorrect(primary_directory, app_data_name)
    # create dictionary for login request
    try:
        login_dict =    {
                        "LoginRq":{
                            "IAID":app_data_dict["IAID"],
                            "IADescription":app_data_dict["IADescription"],
                            "UserName":username,
                            "IAName":app_data_dict["IAName"],
                            "UserPassword":b64_md5_pass
                            }
                        }
    except (KeyError):
        # report error to user and begin termination of program sequence
        return dat_missing_incorrect(primary_directory, app_data_name)
    #wrap and return message
    return wrap_message(key, login_dict)

# perform login function
def login(primary_directory, app_data_name, status_codes_name, username, password):
    # get the login_message
    login_message = make_login_msg(username, password, primary_directory, app_data_name)
    login_response = streams.fishbowl_connection_communicate(login_message, primary_directory, app_data_name)
    #parse reply
    server_reply = parse_reply(login_response, primary_directory, status_codes_name)
    # check if login succesfull or bad credentials
    return server_reply

# sends basic queries to fishbowl and returns the result
def send_query(key, query, primary_directory, app_data_name, status_codes_name):
    # convert query to dict and turn into communication packet
    message_dict = {"ExecuteQueryRq":{"Query":query}}
    data_packet = wrap_message(key, message_dict)
    # send query and capture response
    comm_result = streams.fishbowl_connection_communicate(data_packet, primary_directory, app_data_name)
    parsed_reply = parse_reply(comm_result, primary_directory, status_codes_name)
    # extract results from query, server returns list of strings
    if parsed_reply['status_code'] == 1000:
        query_result = parsed_reply["reply_data"]["ExecuteQueryRs"]["Rows"]["Row"]
        new_list = []
        # seperate strings into list
        # fishbowl does not purge commas, and returns a CSV which may contain commas in data
        # this may cause issues if a result contains ",," or commas next to quotes
        for row in query_result:
            new_list.append(row.replace(",,", "||").replace("\",", "\"|").replace(",\"", ("|\"")).split("|"))
        return new_list
    else:
        return False

# breaks fishbowl reply into useable parts
def parse_reply(server_response, primary_directory, status_codes_name):
    status_response = ""
    codes_dict = {}
    dict_response = json.loads(server_response)
    reply_data= dict_response["FbiJson"]["FbiMsgsRs"]
    key = dict_response["FbiJson"]["Ticket"]["Key"]
    status_code = reply_data["statusCode"]
    # get code dictionary
    try:
        file = open(status_codes_name, "r")
        codes_dict = json.loads(file.read())
    except (FileNotFoundError, OSError) as e:
        dat_missing_incorrect(primary_directory, status_codes_name)
    # try to get status response
    try:
        status_response = codes_dict[str(status_code)]
    except KeyError:
        sys.exit()
    reply_dict = {
        "key":key,
        "status_code":status_code,
        "status_response":status_response,
        "reply_data":reply_data
    }
    return reply_dict

# wrap messages in the json format for fishbowl
def wrap_message    (key, message_dict):
    data_packet =   {
                    "FbiJson":{
                        "Ticket":{
                            "Key":key
                            },
                        "FbiMsgsRq":message_dict
                        }
                    }
    return data_packet


'''
################################################################################
error management
################################################################################
'''
def dat_missing_incorrect (primary_directory, file_name):
    os.exit()
