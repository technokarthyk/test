"""Function for getting the secret key from the key vault"""

import os
import logging
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

def get_secret_from_keyvault(secret_name):
    try:
        keyVaultUrl = os.environ.get("KEYVAULT_URL")
        client_id = os.environ.get("CLIENT_ID")
        credential = ManagedIdentityCredential(client_id=client_id)
        client = SecretClient(vault_url=keyVaultUrl, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception as ex:
        logging.error(f"Error occurred while fetching secret from Key Vault: {ex}")