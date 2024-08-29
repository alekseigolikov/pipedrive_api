import os
import json
import logging
import logging
import argparse
from argparse import RawTextHelpFormatter
import getpass
import json
import sys

#from modules.pipedriveapi import PipedriveREST

__all__ = ['KeyVaultStorage']


class KeyVaultStorage:

    def __init__(self):
        self._token_file_name = 'token.json'
        self._config_file_name = 'config.json'
        self._token = self._get_token_data()
        self._config = self._get_config_data()

    def get_access_token(self):
        return self._get_token_param('access_token')

    def get_refresh_token(self):
        return self._get_token_param('refresh_token')
    
    def get_redirect_uri(self):
        return self._get_config_param('redirect_uri')

    def get_client_id(self):
        return self._get_config_param('client_id')

    def get_client_secret(self):
        return self._get_config_param('client_secret')

    def get_code(self):
        return self._get_config_param('code')


    def _get_token_param(self, param_name):
        output = None
        try:
            output = self._token[param_name]
        except KeyError:
            logging.error(f"Token parameter {param_name} is not defined")
        return output
    
    def _get_config_param(self, param_name):
        output = None
        try:
            output = self._config[param_name]
        except KeyError:
            logging.error(f"Config parameter {param_name} is not defined")
        return output
    
    def _set_config_param(self, param_name, param_value):
        self._config[param_name] = param_value
        self.update_config(self._config)

    def _set_token_param(self, param_name, param_value):
        self._token[param_name] = param_value
        self.update_token(self._token)

    def update_token(self, token_json_dict):
        with open(self._token_file_name, 'w') as token_file:
            json.dump(token_json_dict, token_file, sort_keys=True, indent=4)
            token_file.close()
        self._token = self._get_token_data()

    def update_config(self, config_json_dict):
        with open(self._config_file_name, 'w') as config_file:
            json.dump(config_json_dict, config_file, sort_keys=True, indent=4)
            config_file.close()
        self._config = self._get_config_data()

 
    def show_auth(self):
        """ Show auth params
        """
        auth_type = ''
        auth_value = ''
        example = '''Example:
        pipedrive.py show_auth access-token
        pipedrive.py show_auth refresh-token
        pipedrive.py show_auth client-id
        pipedrive.py show_auth client-secret
        pipedrive.py show_auth code
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Show content of token stored in keyvault", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        parser.add_argument('type', help='Show auth code')
        args = parser.parse_args(sys.argv[2:])

        # get parameters
        if args.type == 'access-token':
            auth_type = 'Access token'
            auth_value = self.get_access_token()
        if args.type == 'refresh-token':
            auth_type = 'Refresh token'
            auth_value = self.get_refresh_token()
        if args.type == 'client-id':
            auth_type = 'Client id'
            auth_value = self.get_client_id()
        if args.type == 'client-secret':
            auth_type = 'Client secret'
            auth_value = self.get_client_secret()
        if args.type == 'code':
            auth_type = 'code'
            auth_value = self.get_code()

        logging.info(f"{auth_type} value : {auth_value}")

    def set_auth(self):
        """ Show auth params
        """
        auth_type = ''
        auth_value = ''
        example = '''Example:
        pipedrive.py set_auth access-token token_value
        pipedrive.py set_auth refresh-token token_value
        pipedrive.py set_auth client-id client_id_value
        pipedrive.py set_auth client-secret client_secret_value
        pipedrive.py set_auth code code_value
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Show content of token stored in keyvault", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        parser.add_argument('type', help='Name of param to set')
        parser.add_argument('value', help='Value of param to set')
        args = parser.parse_args(sys.argv[2:])

        # get parameters
        if args.type == 'access-token':
            auth_type = 'Access token'
            self._set_token_param('access-token', args.value)
        if args.type == 'refresh-token':
            auth_type = 'Refresh token'
            self._set_token_param('refresh-token', args.value)
        if args.type == 'client-id':
            auth_type = 'Client id'
            self._set_config_param('client-id', args.value)
        if args.type == 'client-secret':
            auth_type = 'Client secret'
            self._set_config_param('client-secret', args.value)
        if args.type == 'code':
            auth_type = 'Code'
            self._set_config_param('code', args.value)

        logging.info(f"{auth_type} stored value: {args.value}")


    def _get_token_data(self):
        output = None
        try:
            with open(self._token_file_name, 'r') as token_file:
                output = json.load(token_file)
        except FileNotFoundError:
            logging.error(f"Token File {self._token_file_name} does not exist.")
            pass
        return output
    
    def _get_config_data(self):
        output = None
        try:
            with open(self._config_file_name, 'r') as config_file:
                output = json.load(config_file)
        except FileNotFoundError:
            logging.error(f"Token File {self._config_file_name} does not exist.")
            pass
        return output