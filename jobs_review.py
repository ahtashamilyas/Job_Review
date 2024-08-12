from ai_review import process_row
# from config import users
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from requests import ConnectionError, HTTPError
import random
import time
import datetime


# Set up Google Sheets API credentials
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, 'emails-data-419611-df598de3f127.json')
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(json_file_path, scope)
client = gspread.authorize(creds)


def error_log(worksheet_name, error_message):
    log_filename = os.path.join(script_dir, 'job_review_error_logs.txt')
    with open(log_filename, 'a') as log_file:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f"[{timestamp}] Worksheet: {worksheet_name}\n{error_message}\n\n")

def get_required_client_requirements(worksheet_name):
    max_retries = 5
    backoff_factor = 2
    for retry in range(max_retries):
        try:
            sheet = client.open('DB')
            worksheet = sheet.worksheet(worksheet_name)
            target_title = worksheet.col_values(4)[1:]
            target_location = worksheet.col_values(6)[1:]
            target_industry = worksheet.col_values(5)[1:]
            target_salary = worksheet.col_values(1)[1:]
            previous_exp = worksheet.col_values(2)[1:]
            resume = worksheet.col_values(3)[1:]
            i_dont_have = worksheet.col_values(7)[1:]
            return target_title, target_location, target_industry, target_salary, previous_exp, resume, i_dont_have
        except (ConnectionError, HTTPError, gspread.exceptions.APIError) as e:
            wait_time = backoff_factor ** retry + random.uniform(0, 1)
            error_log(worksheet_name, str(e))
            print(f"Error connecting to Google Sheets API: {e}. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            error_log(worksheet_name, str(e))
            raise
    raise Exception(f"Failed to connect to Google Sheets API after {max_retries} retries")

def process_jobs(start_row_index, num_rows_to_read, worksheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open('Review Sheet')
    worksheet = sheet.worksheet(worksheet_name)
    client_requirements = get_required_client_requirements(worksheet_name)
    for i in range(start_row_index, start_row_index + num_rows_to_read):
        row = worksheet.row_values(i)
        title = row[1]
        location = row[3]
        salary = row[4]
        description = row[6]
        comment = process_row(title, location, salary, description, client_requirements)
        worksheet.update_cell(i, 14, comment) #8

if __name__ == "__main__":
    worksheet_name = input("Enter worksheet name: ")
    start_row_index = int(input("Enter start row index: "))
    num_rows_to_read = int(input("Enter number of rows to read: "))
    process_jobs(start_row_index, num_rows_to_read, worksheet_name)

# if __name__ == "__main__":
#     for user in users:
#         worksheet_name = user['worksheet_name']
#         start_row_index = int(input("Enter start row index: "))
#         num_rows_to_read = int(input("Enter number of rows to read: "))
#         process_jobs(start_row_index, num_rows_to_read, worksheet_name)