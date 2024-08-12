import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import time
from requests.exceptions import ConnectionError, HTTPError

class GoogleSheetsAPI:
    def __init__(self, json_file_paths):
        self.json_file_paths = json_file_paths
        self.current_index = 0
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.client = self._authorize()

    def _authorize(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_file_paths[self.current_index], self.scope)
        return gspread.authorize(creds)

    def switch_api_key(self):
        self.current_index = (self.current_index + 1) % len(self.json_file_paths)
        self.client = self._authorize()

    def exponential_backoff_request(self, func, *args, max_retries=5, backoff_factor=2, **kwargs):
        for retry in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, HTTPError, gspread.exceptions.APIError) as e:
                if retry == max_retries - 1:
                    raise e
                wait_time = backoff_factor ** retry + random.uniform(0, 1)
                print(f"Error: {e}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                self.switch_api_key()

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        return self.exponential_backoff_request(
            self.client.open(spreadsheet_name).worksheet, worksheet_name
        )