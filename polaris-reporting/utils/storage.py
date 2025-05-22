"""Functions for connecting the blob and queue storage """ 

from azure.storage.blob import BlobServiceClient
from utils.keyvault import get_secret_from_keyvault
import logging
import json

def get_blob_Storage_Conn():
  try:
    connection_string = get_secret_from_keyvault("StorageConnectionString")
    container_name = get_secret_from_keyvault("BlobContainerName")
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    return container_client
 
  except Exception as e:
        logging.error(f"Error in connecting the blob_storage: {str(e)}")

def read_blob_file(filepath):
    try:
        container_client = get_blob_Storage_Conn()
        blob_client = container_client.get_blob_client(filepath)
        if blob_client:
            try:
                blob_data = blob_client.download_blob()
                blob_content = blob_data.readall()
                content = json.loads(blob_content.decode('utf-8'))
                return content
            except Exception as ex:
                logging.error('Error in reading blob data: %s', str(ex))
        else:
            return None

    except Exception as ex:
        logging.error('Error reading blob file: %s', str(ex))
        return None

def write_blob_file(blob_name, data):
    try:
      container_client = get_blob_Storage_Conn()
      blob_client = container_client.get_blob_client(blob_name)
      blob_client.upload_blob(data, overwrite=True)       
      return True
    except Exception as e:
       logging.error(f"file writing issue occured: {e}")
       return None
    

def read_error_dictionary(file_path="", type=None):
    try:
        container_client = get_blob_Storage_Conn()
        blob_client = container_client.get_blob_client(file_path)
        if blob_client:
            try:
                blob_data = blob_client.download_blob()
                blob_content = blob_data.readall()
                content = json.loads(blob_content.decode('utf-8'))
                if type:
                  return content['error_definition'][type]
                return content
            except Exception as ex:
                logging.error('Error in reading blob data: %s', str(ex))
        else:
            return None

    except Exception as ex:
        logging.error('Error reading blob file: %s', str(ex))
        return None

def read_client_global_config(file_path):
    try:
        container_client = get_blob_Storage_Conn()
        blob_client = container_client.get_blob_client(file_path)
        if blob_client:
            try:
                blob_data = blob_client.download_blob()
                blob_content = blob_data.readall()
                content = json.loads(blob_content.decode('utf-8'))
                return content
            except Exception as ex:
                logging.error('Error in reading blob data: %s', str(ex))
        else:
            return None

    except Exception as ex:
        logging.error('Error reading blob file: %s', str(ex))
        return None

# function to create the folder path
def create_folder_in_blob_storage(container_client, folder_path):
    try:
        if not container_client.exists():
            container_client.create_container()
        blob_client = container_client.get_blob_client(f"{folder_path}/.txt")
        if not blob_client.exists():
            blob_client.upload_blob(b'', overwrite=True)
            print(f"Folder '{folder_path}' created successfully.")
        else:
            print(f"Folder '{folder_path}' already exists.")
    except Exception as e:
        print(f"An error occurred while creating folder: {e}")