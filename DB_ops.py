import MySQLdb
from MySQLdb.cursors import DictCursor
from MySQLdb import Error
import datetime
import os


script_dir = os.path.dirname(os.path.abspath(__file__))

def error_log(worksheet_name, error_message, job_board):
    log_filename = os.path.join(script_dir, 'error_logs.txt')
    with open(log_filename, 'a') as log_file:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f"[{timestamp}] Worksheet: {worksheet_name}, Job Board: {job_board}\n{error_message}\n\n")


def write_job_data_to_mysql(jobs_data, candidate_id, connection):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO candidate_jobs_list (candidate_id, position_title, company, location, salary, job_link, job_description, job_ai_review, created_at) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    job_records = [(candidate_id, job['position_title'], job['company'], job['location'], job['salary'], job['job_link'], job['job_description'], job['job_ai_review'], job['created_at']) for job in jobs_data]
    cursor.executemany(insert_query, job_records)
    connection.commit()

def mark_jobs_as_processed(job_ids, connection):
    cursor = connection.cursor()
    format_strings = ','.join(['%s'] * len(job_ids))
    update_query = f"UPDATE candidate_jobs_list SET processed = True WHERE id IN ({format_strings})"
    cursor.execute(update_query, tuple(job_ids))
    connection.commit()

def retrieve_job_data_from_mysql(candidate_id, connection):
    cursor = connection.cursor(cursorclass=DictCursor)  # For localhost
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    select_query = """
    SELECT * 
    FROM candidate_jobs_list    
    WHERE candidate_id = %s 
      AND processed = FALSE 
      AND Date(created_at) = %s
      AND (position_title, company) NOT IN (
          SELECT position_title, company 
          FROM candidate_jobs_list  
          WHERE candidate_id = %s 
            AND processed = TRUE 
            AND Date(created_at) BETWEEN %s AND %s
      )
    """
    
    cursor.execute(select_query, (candidate_id, today, candidate_id, thirty_days_ago, today))
    rows = cursor.fetchall()
    cursor.close()
    return rows

def retrieve_processed_job_data_from_mysql(candidate_id, connection):
    cursor = connection.cursor(cursorclass=DictCursor)  # For localhost
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    select_query = """
    SELECT position_title, company 
    FROM candidate_jobs_list
    WHERE candidate_id = %s
      AND processed = TRUE
      AND Date(created_at) BETWEEN %s AND %s
    """
    
    cursor.execute(select_query, (candidate_id, thirty_days_ago, today))
    processed_jobs = cursor.fetchall()
    
    # Convert list of dictionaries to set of tuples
    processed_jobs_set = set((job['position_title'], job['company']) for job in processed_jobs)
    return processed_jobs_set

def create_connection(is_remote):
    try:
        connection = MySQLdb.connect(
        host="localhost",
        user="root",
        password="",
        database="candidateside"
    )
        return connection
    except Error as e:
        print(f"The error '{e}' occurred")
        return None