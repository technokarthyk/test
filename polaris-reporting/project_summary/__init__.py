"""
project summary generate and retrieve the information api
"""
import logging 
import json
import azure.functions as func
from utils.common_functions import error_response, load_config_info
from .summary_info import Summary

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        #load the required config info
        config_info = load_config_info()
        config = config_info[0]
        error_code_filepath = config_info[1]

        summary = Summary(config, error_code_filepath)

        route = req.route_params.get('route')
        method = req.method

        match (method, route):

            case ('GET', route) if route.startswith('generate/'):
                clientId = route.split('/')[-1]
                data = summary.generate_summary(clientId=clientId) #generate summary information
                # data = summary.generate_details(clientId=clientId)
            case ('GET', 'retrieve/all'):
                daterange = req.params.get('daterange')
                data = summary.retrieve_summary(daterange=daterange) #Retrieve the summary report for all client
            case ('GET', route) if route.startswith('retrieve/client/'):
                clientId = route.split('/')[-1]
                daterange = req.params.get('daterange')
                data = summary.retrieve_summary(clientId=clientId, daterange=daterange) #Retrieve the summary report for specific client               
            case _:
                data = error_response(
                    file_path=error_code_filepath,
                    type=config.get('Validation'),
                    code='CLI-VAL-1006'
                    )                    
        return func.HttpResponse(body=json.dumps(data), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.error(f"Main function exception: {e}")
        error = error_response(
            file_path=error_code_filepath, 
            type=config.get('ExecException'), 
            code='exec-except-1000'
            )
        return func.HttpResponse(body=json.dumps(error), mimetype="application/json", status_code=200)
