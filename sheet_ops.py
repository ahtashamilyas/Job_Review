import os
from api_handler import GoogleSheetsAPI
import gspread
from DB_ops import create_connection, mark_jobs_as_processed


script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_paths = [
    os.path.join(script_dir, 'emails-data-419611-df598de3f127.json'),
    os.path.join(script_dir, 'jobs-data-420405-8e741dfe8df5.json')  # Add more credential files if available
]
google_sheets_api = GoogleSheetsAPI(json_file_paths)

# Mapping of job boards to their corresponding column numbers for URLs
job_board_columns = {
    'SimplyHired': 2,
    'LinkedIn': 4,
    'Glassdoor': 6,
    'Indeed': 8,
    'Hiring Cafe': 12,
    'Google': 14
}

def get_base_urls(worksheet_name, job_board):
    retries = 3  # Number of retries before giving up
    for attempt in range(retries):
        try:
            if job_board in job_board_columns:
                column_number = job_board_columns[job_board]
            else:
                raise ValueError(f"Unknown job board: {job_board}")
            worksheet = google_sheets_api.exponential_backoff_request(
                google_sheets_api.get_worksheet, 'List of URLs', worksheet_name
            )
            return worksheet.col_values(column_number)[1:]
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:  # Quota exceeded error
                if attempt < retries - 1:
                    # Switch to the next API key
                    google_sheets_api.switch_api_key()
                    print(f"Switched to the next API key. Retrying...")
                    continue  # Retry with the next API key
                else:
                    raise  # If retries are exhausted, raise the exception
            else:
                raise  # Re-raise any other API errors

def get_required_client_requirements(worksheet_name):
    retries = 3  # Number of retries before giving up
    for attempt in range(retries):
        try:
            worksheet = google_sheets_api.get_worksheet('DB', worksheet_name)
            target_title = worksheet.col_values(4)[1:]
            target_location = worksheet.col_values(6)[1:]
            target_industry = worksheet.col_values(5)[1:]
            target_salary = worksheet.col_values(1)[1:]
            previous_exp = worksheet.col_values(2)[1:]
            resume = worksheet.col_values(3)[1:]
            i_dont_have = worksheet.col_values(7)[1:]
            return target_title, target_location, target_industry, target_salary, previous_exp, resume, i_dont_have
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:  # Quota exceeded error
                if attempt < retries - 1:
                    # Switch to the next API key
                    google_sheets_api.switch_api_key()
                    print(f"Switched to the next API key.")
                    continue  # Retry with the next API key
                else:
                    raise  # If retries are exhausted, raise the exception
            else:
                raise  # Re-raise any other API errors


def write_job_data_to_google_sheet(jobs_data, worksheet_name, is_remote):
    worksheet = google_sheets_api.get_worksheet('Review Sheet', worksheet_name)
    next_row = len(worksheet.col_values(2)) + 1
    required_rows = next_row + len(jobs_data) - 1
    num_current_rows = worksheet.row_count
    if required_rows > num_current_rows:
        additional_rows_needed = required_rows - num_current_rows
        worksheet.add_rows(additional_rows_needed)
    rows_to_update = []
    for job in jobs_data:
        date_column_iso = job['created_at'].strftime('%m/%d/%Y')
        row_values = [date_column_iso, job['position_title'], job['company'], job['location'], job['salary'], job['job_link'], job['job_ai_review']]
        rows_to_update.append(row_values)
    start_cell = f'A{next_row}'
    end_cell = f'H{next_row + len(jobs_data) - 1}'
    cell_range = f'{start_cell}:{end_cell}'
    
    worksheet.update(range_name=cell_range, values=rows_to_update, value_input_option='USER_ENTERED')
    # Mark jobs as processed in the database
    job_ids = [job['id'] for job in jobs_data]
    if job_ids:
        connection = create_connection(is_remote)
        mark_jobs_as_processed(job_ids, connection)

