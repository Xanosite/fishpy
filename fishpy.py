import sys
import os
import streams
import api

def get_data_files():
    primary_directory = os.getcwd()
    app_data_name = primary_directory + "/data/application-data.dat"
    status_codes_name = primary_directory + "/data/status-codes.dat"
    return [primary_directory, app_data_name, status_codes_name]

# returns [True, 'key'] or False
def login(username, password):
        key = None
        login_response_data = {}
        files = get_data_files()
        # login and get initial data
        login_response_data = api.login(files[0], files[1], files[2], username, password)
        if login_response_data["status_code"] == 1000:
            key = login_response_data["key"]
            return [True, key]
        else:
            return False

# returns query results as list, or False if there is an error
def query(key, query):
    files = get_data_files()
    return api.send_query(key, query, files[0], files[1], files[2])

# logs out key, returns true on succesful logout, other codes return false
def logout(key):
    files = get_data_files()
    return api.logout(key, files[0], files[1], files[2])
