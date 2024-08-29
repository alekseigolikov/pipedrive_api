#!/usr/bin/python3
import json
import logging
import argparse
import sys
import datetime
import os
import csv
import argparse
from argparse import RawTextHelpFormatter

from modules.pipedriveapi import PipedriveREST, PipedriveCLI, PipedriveDeals
from modules.keyvault import KeyVaultStorage
__all__ = ['FileLoad']

class FileLoad:
    def __init__(self):
        self._file_name = 'data.csv'
        self._deal_api = PipedriveDeals()
    
    def load_file(self):
        """ Load data after transformation to pipedrive backend
        """
        example = '''Example:
        pipedrive.py load_file path_to_csv_extracted_after_transformation
                 '''
        # command arguments
        parser = argparse.ArgumentParser(description="Load data to Pipedrive", epilog=example, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-v', '--verbose', help='Debug level login to console', action='store_true', default=False)
        parser.add_argument('filename', help='path to csv file to load to Pipedrive')
        args = parser.parse_args(sys.argv[2:])

        self._file_name = args.filename

        with open(self._file_name) as file_in:
            for line in file_in:
                title, status, value = line.split(",")
                code, text = self._deal_api.add_deal({  "title":title, "status":status, "value":value })
                logging.debug(f"Loading request result code {code} Text {text}")
                if code == 200:
                    logging.info(f'{title} order is loaded to Pipedrive')
                else:
                    logging.error(f'Load of {title} failed with {text}')

