"""Common functions for getting the time period related details"""

import logging
from datetime import datetime, timezone
from utils.database import get_cosmosdb_client
from utils.keyvault import get_secret_from_keyvault
from utils.storage import read_error_dictionary, read_client_global_config


#Standard format for the json response
def json_response(data=[], msg="", state="", code=200):
    return {
                "data": data,
                "message": msg,
                "status": state,
                "code": code
            }

#Standard format for the json response
def success_response(data=[], response=""):
    return {
                "data": data,
                "error": [],
                "response": response,
                "status": "ok"
            }

def error_format(code="", description="", type="", details=""):
    return {
            "data": [],
            "error": {
                "code": code,
                "description": description,
                "type": type,
                "details": details
            },
            "response": "",
            "status": "error"
    }

#error_response
#file_path: error dictionary file path
#service: microservice name
#category: validation or functional
#code: error status code
#description: description about the error
#type: validation or functional
#details: details
def error_response(file_path="", type="", code="", description="", details=""):
    error_dict = read_error_dictionary(file_path=file_path, type=type)
    if description != "" and details != "":
        return error_format(code=code, description=description, type=type, details=details)
    elif description != "":
        return error_format(code=code, description=description, type=type, details=error_dict[code])
    elif details != "":
        return error_format(code=code, description=error_dict[code], type=type, details=details)
    return error_format(code=code, description=error_dict[code], type=type, details=error_dict[code])

def load_config_info():
    folder_path = f"{get_secret_from_keyvault('rootFolderAdmin')}/{get_secret_from_keyvault('referenceFolder')}"
    global_config_filepath = f"{folder_path}/{get_secret_from_keyvault('ClientGlobalConfig')}"
    config = read_client_global_config(global_config_filepath)
    error_code_filepath = f"{folder_path}/{get_secret_from_keyvault('ErrorDictionary')}"
    return config, error_code_filepath



def get_utc_dates():
    # Get today's date in UTC
    today_date_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Get the first day of the current month in UTC
    month_start_date_utc = today_date_utc.replace(day=1)

    # Get the first day of the current year in UTC
    year_start_date_utc = today_date_utc.replace(day=1, month=1)

    return today_date_utc, month_start_date_utc, year_start_date_utc
