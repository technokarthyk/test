"""Common functions for getting the container related details"""

import logging
from azure.cosmos import CosmosClient
from utils.keyvault import get_secret_from_keyvault

def get_cosmosdb_client():
    try:
        cosmos_db_endpoint = get_secret_from_keyvault("CosmosDbEndPoint")
        cosmos_db_key =get_secret_from_keyvault("CosmosDbKey")
        database_name = get_secret_from_keyvault("DataBaseName")
        client = CosmosClient(cosmos_db_endpoint, cosmos_db_key)
        database = client.get_database_client(database_name) 
        return database
    except Exception as e:
        logging.error(f"Error in connecting to cosmos db : {str(e)}")


#get the query data
def get_query_data(query, **kwargs):
  key = kwargs.get('key', "")
  try:  
    database = get_cosmosdb_client()
    match key:
        case "client":
            container_name = get_secret_from_keyvault("ClientContainer")
        case 'projects':
            container_name = get_secret_from_keyvault("Projects")    
        case 'task':
            container_name = get_secret_from_keyvault("TaskContainer")
        case 'urls':
            container_name = get_secret_from_keyvault("UrlCatalogContainer")
        case 'task_exe':
            container_name = get_secret_from_keyvault("TaskExeContainer")
        case 'summary':
            container_name = get_secret_from_keyvault("webScrapingSummaryContainer")
        case 'webscraping_analytics':
            container_name = get_secret_from_keyvault("WebscrapingAnalyticsContainer")
        case 'document_catalog':
            container_name = get_secret_from_keyvault("DocumentCatelogContainer")    
    container = database.get_container_client(container_name)
    container_result = list(container.query_items(query=query, enable_cross_partition_query=True))
    return container_result
  except Exception as e:
        logging.error(f"Error in getting query data : {str(e)}")

#get container info
def manage_container(**kwargs):
  key = kwargs.get('key', "")
  action = kwargs.get('action', '')
  body = kwargs.get('body', '')
  item = kwargs.get('item', '')
  uniqueId = kwargs.get('uniqueId', '')
  partitionKey = kwargs.get('partitionKey', '')

  try:  
    database = get_cosmosdb_client()
    match key:
        case "client":
            container_name = get_secret_from_keyvault("ClientContainer")
        case 'projects':
            container_name = get_secret_from_keyvault("Projects")    
        case 'document_catalog':
            container_name = get_secret_from_keyvault("DocumentCatelogContainer")    
        case 'summary':
            container_name = get_secret_from_keyvault("webScrapingSummaryContainer")
        case 'webscraping_analytics':
            container_name = get_secret_from_keyvault("WebscrapingAnalyticsContainer")
    container = database.get_container_client(container_name)

    match action:
        case "read":
            data = container.read_item(item=uniqueId, partition_key=partitionKey)
            return data
        case "create":
            container.create_item(body=body)
            return True
        case "update":
            container.replace_item(item=item, body=item)
            return True
        case 'upsert':
            container.upsert_item(body)
            return True
        case _:
            return None

  except Exception as e:
        logging.error(f"Error in getting container data : {str(e)}") 
        return None