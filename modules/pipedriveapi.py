import os
import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib
import argparse
from argparse import RawTextHelpFormatter
import sys

from modules.keyvault import KeyVaultStorage

__all__ = ['PipedriveCLI','PipedriveREST','PipedriveUser','PipedriveDeals']

OAUTH_URI = "https://oauth.pipedrive.com/oauth/token"

API_URI_V1 = "https://api-proxy.pipedrive.com/api/v1/"
API_URI_V2 = "https://api-proxy.pipedrive.com/api/v2/"

class PipedriveCLI:
    def __init__(self):
        self._kv = KeyVaultStorage()
        self._restapi = PipedriveREST()

    def fetch_token(self):
        """ Fetch new token
        """

        example = '''Example:
        pipedrive.py fetch_token
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Fetch new token", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[2:])

        code, content = self._restapi._get_token()
        logging.debug(f"Answer for token request: {code}, {content}")

        if code == 200:
            self._kv.update_token(json.loads(content))
            logging.debug(f"New token value: {content}")
            logging.info(f"Token request successfully finished")
        else:
            logging.error(f"Token request failed with code: {code} Error: {content}")


    def refresh_token(self):
        """ Refreshes token
        """

        example = '''Example:
        pipedrive.py refresh_token
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Triger token refresh and store it", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[2:])


        code, content = self._restapi._do_token_refresh()
        logging.debug(f"Answer for token refresh: {code}, {content}")

        if code == 200:
            self._kv.update_token(json.loads(content))
            logging.debug(f"New token value: {content}")
            logging.info(f"Token refresh successfully finished")
        else:
            logging.error(f"Token refresh failed with code: {code} Error: {content}")


    def whoami(self):
        """ Lookup current user
        """

        example = '''Example:
        pipedrive.py whoami
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Lookup info on user owning token", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[2:])

        userapi = PipedriveUser()
        code, content = userapi.whoami()
        logging.debug(f"Answer for user query: {code}, {content}")

        if code == 200:
            logging.info(f"Current user info: {content}")
        else:
            logging.error(f"User request failed with code: {code} Error: {content}")



    def deals(self):
        """ manage deals
        """

        example = '''Example:
        pipedrive.py deals
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="List all deals", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[2:])

        dealsapi = PipedriveDeals()
        code, content = dealsapi.get_all_deals()
        logging.debug(f"Answer for deals query: {code}, {content}")

        if code == 200:
            logging.info(f"Deals available: {content}")
        else:
            logging.error(f"Deals query failed: {code} Error: {content}")

class PipedriveREST:

    def __init__(self):
        self._token_file_name = 'token.json'
        self._config_file_name = 'config.json'
        self._kv = KeyVaultStorage()
        self._access_token = self._kv.get_access_token()
        self._refresh_token = self._kv.get_refresh_token()
        self._redirect_uri = self._kv.get_redirect_uri()
        self._code = self._kv.get_code()
        self._config = self._get_config_data()
        self._failed_auth_counter = 0
        self._token_autorefresh = ( self._config['token_autorefresh'] == 1 )
    
    def _get_config_data(self):
        output = None
        try:
            with open(self._config_file_name, 'r') as config_file:
                output = json.load(config_file)
        except FileNotFoundError:
            logging.error(f"Config File {self._config_file_name} does not exist.")
            pass
        return output

    def _get_token(self, code = None):
        if code == None:
            code = self._code
        request = {"grant_type": "authorization_code",
            "redirect_uri": self._redirect_uri,
            "code": code}
        response = self.post_request(OAUTH_URI, request, 'basic')
        return response
    
    def _do_token_refresh(self):
        request = {"grant_type": "refresh_token",
            "refresh_token": self._refresh_token}
        response = self.post_request(OAUTH_URI, request, 'basic')
        return response
    
    def _auto_refresh_token(self):
        self._failed_auth_counter = None
        #request = {"grant_type": "refresh_token",
        #    "refresh_token": self._refresh_token}
        #response = self.post_request(OAUTH_URI, request, 'basic')
        response = self._do_token_refresh()
        code = response[0]
        content = response[1]
        if code == 200:
            self._kv.update_token(json.loads(content))
            self._access_token = self._kv.get_access_token()
            self._failed_auth_counter = 0
        return self._failed_auth_counter == 0

    def post_request(self, uri, data, auth):
        if auth == 'basic':
            response = requests.post(uri, auth=HTTPBasicAuth(self._config['client_id'], self._config['client_secret']), data = data)
        else:
            headers = {"Authorization": f"Bearer {self._access_token}", "Content-type": "application/json"}
            response = requests.post(uri, headers=headers, data = data)

        code = response.status_code
        content = response.content.decode('utf-8')
        if int(code) == 401 and self._autorefresh_is_enabled():
            logging.debug(f'Possible token expiry, triggering  autorefresh')
            self._auto_refresh_token()
            code, content = self.post_request(self, uri, data, auth)
        return (code, content)

    def get_request(self, uri, get_params_dict = None):
        headers = {"Authorization": f"Bearer {self._access_token}"}
        if get_params_dict:
            uri = uri + "?" + self._build_get_params(get_params_dict)
        response = requests.get(uri, headers=headers)
        
        code = response.status_code
        content = response.content.decode('utf-8')
        if int(code) == 401 and self._autorefresh_is_enabled():
            logging.debug(f'Possible token expiry, triggering  autorefresh')
            self._auto_refresh_token()
            code, content = self.get_request(uri)
        return (code, content)
    
    def _build_get_params(self, get_params_dict):
        out = urllib.urlencode(get_params_dict)
        return out

    def _autorefresh_is_enabled(self):
        return self._token_autorefresh and self._failed_auth_counter == 0
    
    def fetch_token(self):
        """ Show auth params
        """

        example = '''Example:
        pipedrive.py fetch_token
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Show content of token stored in keyvault", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[2:])
        new_token = self._get_token()
        logging.debug(f"New Token: {new_token}")


    def refresh_token(self):
        """ Show auth params
        """

        example = '''Example:
        pipedrive.py fetch_token
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Show content of token stored in keyvault", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        args = parser.parse_args(sys.argv[2:])

        #new_token = self._do_token_refresh()
        #logging.debug(f"New Token: {new_token}")

        response = self._do_token_refresh()
        logging.debug(f"Answer for token refresh: {response}")
        code = response[0]
        content = response[1]
        #content = response.content.decode('utf-8')

        if code == 200:
            self._kv.update_token(json.loads(content))
            self._access_token = self._kv.get_access_token()
            self._failed_auth_counter = 0
            logging.debug(f"New token value: {content}")
            logging.info(f"Token refresh successfully finished")
        else:
            logging.error(f"Token refresh failed with code: {code} Error: {content}")

class PipedriveUser:

    def __init__(self):
        self._username = None

    def whoami(self):
        output = None
        request = API_URI_V1 + "users/me"
        request_code, request_content = PipedriveREST().get_request(request)
        #if request_code == 200:
        #    output = json.loads(request_content)
        return request_code, request_content

class PipedriveDeals:
    def __init__(self):
        pass

    def get_all_deals(self, params_dict = None):
        request = API_URI_V2 + "deals"
        request_code, request_content = PipedriveREST().get_request(request)
        return request_code, request_content

    def add_deal(self, params_dict):
        request = API_URI_V2 + "deals"
        data = json.dumps(params_dict)
        request_code, request_content = PipedriveREST().post_request(request, data, 'oauth')
        return request_code, request_content

    def find_deal(self, params_dict):
        request = API_URI_V2 + "deals"
        data = json.dumps(params_dict)
        request_code, request_content = PipedriveREST().post_request(request, data, 'oauth')
        return request_code, request_content
