from datetime import datetime, timedelta
import pytz
from flask import Flask, request
from typing import Dict
from flask_cors import CORS
import dotenv
import time
from azure.storage.blob import BlobServiceClient
import os
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient
from openai import AzureOpenAI
from flask_socketio import SocketIO
import os
import uuid
from azure.data.tables import TableEntity, UpdateMode
import time
from datetime import datetime
import threading
from vso import *
from model_specs import *
import re

dotenv.load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000", 
    "https://auto-vso.azurewebsites.net"
]}})
socketio = SocketIO(app)

gpt_client = AzureOpenAI(
    azure_endpoint=OPENAI_INSTANCE,
    api_key=os.getenv('API_KEY'),
    api_version=OPENAI_API_VERSION
)

STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')
AZURE_TABLES_CLIENT = table_service_client = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
EMAIL_METADATA_TABLE_CLIENT = table_service_client.get_table_client(table_name='MaintenanceEmailMetadata')
MAINTENANCE_TABLE_CLIENT = table_service_client.get_table_client(table_name='MaintenanceDetails')

EMAIL_SUMMARY_HEADERS = ['CircuitIds', 'StartDatetime', 'EndDatetime', 'NotificationType', 'MaintenanceReason', 'GeographicLocation', 'ISP', 'VsoId']
FAILURE_TO_SUMMARIZE_TSV = """CircuitIds\tStartDatetime\tEndDatetime\tNotificationType\tMaintenanceReason\tGeographicLocation\tISP\tVsoIds
Failure to summarize\tFailure to summarize\tFailure to summarize\tFailure to summarize\tFailure to summarize\tFailure to summarize\tFailure to summarize\tFailure to summarize
"""

def summarize_emails_in_range(start, end):
    email_dict = emails_by_time_range(start, end)
    ids = [f"'{id}'" for id in email_dict]

    return summarize_emails(ids)

def generate_summaries_periodically():
    while True:
        try:
            # Make summaries for past 80 minutes
            num_minutes = 80
            now = datetime.now(pytz.utc)
            then = datetime.now(pytz.utc) - timedelta(minutes=num_minutes)
            sums = summarize_emails_in_range(then.isoformat(), now.isoformat())
            print(f"Summarized {len(sums)} emails from the past {num_minutes} minutes")

            # Check for new summaries to make every 60 minutes
            time.sleep(360)
        except Exception as e:
            print(e)   

def generate_vsos_periodically():
    # wait a bit before checking so that it doesn't start at the same time as summary generation
    time.sleep(10)
    while True:
        try:
            # Make summaries for past 80 minutes
            num_minutes = 80
            now = datetime.now(pytz.utc)
            then = datetime.now(pytz.utc) - timedelta(minutes=num_minutes)
            email_dict = emails_by_time_range(then.isoformat(), now.isoformat())
            if len(email_dict.keys()) > 0:
                vso_ids = get_vso_ids_for_emails(email_dict.keys())
            print(f"Made {len(vso_ids)} vsos from the past {num_minutes} minutes of emails: {vso_ids}")

            # Check for new summaries to make every 60 minutes
            time.sleep(360)
        except Exception as e:
            print(e)  

def emails_by_time_range(start_time, end_time):
    query_filter = f"TimeReceived ge '{start_time}' and TimeReceived le '{end_time}'"
    entities = EMAIL_METADATA_TABLE_CLIENT.query_entities(query_filter)
    info = {
        entity['RowKey']: {
            'TimeReceived': entity['TimeReceived'],
            'Subject': entity['Subject'],
            'From': entity['From'],
        } for entity in entities
    }
    return info

def get_blob_client(connection_string, container_name, blob_name):
    """
    Returns a blob client for the specified blob in Azure Blob Storage.

    :param connection_string: The connection string to the Azure Storage account.
    :param container_name: The name of the container in which the blob resides.
    :param blob_name: The name of the blob to access.
    :return: BlobClient for the specified blob.
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    return blob_client

def parse_html_blob(html_content):
    """
    Parses an HTML blob and returns the text of each tag.
    """
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text from body as one string
    body_text = soup.body.get_text(strip=True) if soup.body else None

    return body_text

def summarize_email(email_id, email_html):
    try:
        res = gpt_client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": email_html},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        return res.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing email {email_id}: {e}")
        return FAILURE_TO_SUMMARIZE_TSV
    
def generate_new_summary(email_id):
    blob_client = get_blob_client(STORAGE_CONNECTION_STRING, 'emails', email_id)
    blob_data = blob_client.download_blob().readall()
    email_body_text = blob_data.decode('utf-8')

    # Check if format is HTML or not; if so, get the pure body text 
    query_filter = f"RowKey eq '{email_id}'"
    entities = EMAIL_METADATA_TABLE_CLIENT.query_entities(query_filter)
    for ent in entities:
        if ent["IsHtml"] == "True":
            html_content = blob_data.decode('utf-8')
            email_body_text = parse_html_blob(html_content)
    
    print(f"Email body for {email_id} retrieved for new summary")
    summary_tsv = summarize_email(email_id, email_body_text)
    print(f"Generated new summary for email {email_id}")
    summaries = upload_email_summary(summary_tsv, email_id)
    print(f"Uploaded new summary for email {email_id}")
    return summaries

# Given email IDs, summarize them and upload summaries to table storage
def summarize_emails(ids):
    all_summaries = []
    try:
        for id in ids:
            clean_id = id.replace("'", "")
            if not clean_id or clean_id.isspace():
                continue

            # Check if summaries already exist
            query_filter = f"EmailId eq '{clean_id}'"
            entities = MAINTENANCE_TABLE_CLIENT.query_entities(query_filter)
            entity_list = [ent for ent in entities]

            if len(entity_list) > 0:
                print(f"Found existing summaries for email {clean_id}: {[ent['RowKey'] for ent in entity_list]}")
                all_summaries.append(entity_list)
                continue
        
            print(f"No summaries found for email {clean_id}")
            summaries = generate_new_summary(clean_id)
            all_summaries.append(summaries)

            print(f"Summaries for email {clean_id} generated: {[ent['RowKey'] for ent in summaries]}")
    except Exception as e:
        print(e)
    
    return all_summaries

# Given AI generated summary, upload it to table storage
def upload_email_summary(summary, email_id):
    summaries = []
    try:
        rows = summary.split('\n')
        for row in rows[1:]:
            values = row.split("\t")
            row_key = str(uuid.uuid4())
            new_entity = {}
            
            for header, val in zip(EMAIL_SUMMARY_HEADERS, values):
                print(f"{header} {val}")
                new_entity[header] = val

            new_entity["RowKey"] = row_key
            new_entity["PartitionKey"] = row_key
            new_entity["EmailId"] = email_id

            summaries.append(new_entity)
            MAINTENANCE_TABLE_CLIENT.create_entity(entity=TableEntity(**new_entity))
    except Exception as e:
        print(f"Failure to upload summary for email {email_id}: {e}")

    return summaries

# Get email sender and subject line
def get_email_info(email_id):
    query_filter = f"RowKey eq '{email_id}'"
    entities = EMAIL_METADATA_TABLE_CLIENT.query_entities(query_filter)
    for row in entities:
        provider_email = row['From']
        subject = row['Subject']
        return provider_email, subject
    return None, None

# From string to list of times
def get_time_strings(s):
    return re.split(r'\s*,\s*', s)

def is_notification_type_new_maintenance(notif_type):
    res = gpt_client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": """Each message you receive is the notification type for a fiber optical cable provider email.
                 If the notification implies that a new maintenance has been scheduled, return true. Examples of notification types
                 that imply a new maintenance include: 'Maintenance scheduled', 'Planned maintenance', 'New maintenance'.
                 Otherwise, return false. Examples of notification types that don't imply a new maintenance include: 'Maintenance completed',
                 'Pending maintenance', 'Reschedule Notification', 'Service restored', 'Technician dispatched', 'Reminder of upcoming maintenance'. 
                 If you can't determine whether it's a new maintenance, return false by default.

                 Only return either true or false as an output.
                """},
                {"role": "user", "content": notif_type},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    return res.choices[0].message.content

# Retrieve existing VSO for maintenance, or create a new one if there is none
def get_or_create_vsos(activity_id):
    # Get table row for that summary. Should only be 1 since this ID
    # is created upon summary generation
    query_filter = f"RowKey eq '{activity_id}'"
    entities = MAINTENANCE_TABLE_CLIENT.query_entities(query_filter)
    sorted_entities = sorted(entities, key=lambda x: x.Timestamp, reverse=True)

    try:
        new_vsos = []
        for row in sorted_entities:
            if "VsoIds" in row:
                existing_vsos = re.split(r'\s*,\s*', row["VsoIds"])
                if existing_vsos:
                    # Existing VSO exists
                    print(f"Found existing VSOs {existing_vsos} for summary {activity_id}")
                    return existing_vsos
            else:
                # Create new VSO if this notification is for new maintenance
                is_new = is_notification_type_new_maintenance(row['NotificationType'])
                if "true" in is_new.lower():
                    email_id = row['EmailId']
                    circuit_ids = row['CircuitIds'].split(",")

                    from_email, subject = get_email_info(email_id)
                    devices = get_devices_for_circuits(circuit_ids)

                    # Create a new VSO for each pair of start/end times for this summary
                    start_times = get_time_strings(row['StartDatetime'])
                    end_times = get_time_strings(row['EndDatetime'])
                    for start, end in zip(start_times, end_times):
                        reason = row['MaintenanceReason']
                        location = row['GeographicLocation']
                        description = f"{location}\n{reason}\n\n{subject}" # TODO: enhance with email metadata and body text

                        new_vso = create_new_maintenance_vso(from_email, start, end, circuit_ids, devices, description, location)
                        new_vso_id = new_vso.id
                        print(f"Created new VSO {new_vso_id} from email summary {activity_id}")
                        
                        new_vsos.append(new_vso_id)

                    print(new_vsos)

                    # Update summary table with new VSO IDs
                    updated_entity = {
                        'PartitionKey': row['PartitionKey'],
                        'RowKey': row['RowKey'],
                        'VsoIds': ",".join(map(str, new_vsos))
                    }
                    MAINTENANCE_TABLE_CLIENT.update_entity(mode=UpdateMode.MERGE, entity=updated_entity)
                    print(f"Updated email summary table row {activity_id} with new VSO IDs: {new_vsos}")
                else:
                    print(f"Email summary {activity_id} notification type is {row['NotificationType']}, not making VSO for it")
                return new_vsos
            break # Only check the one most recent summary in table storage
                    
        print(f"No summary found for {activity_id} while attempting VSO creation")
        return []

    except Exception as e:
        print(f"Failed to create VSO for summary ID {activity_id}: {e}")
        
    return []

    
# Get summaries from email IDs and make new ones if needed
# Then make new VSOs if needed or get existing ones and return the IDs of them
def get_vso_ids_for_emails(ids):
    print(f"Getting VSOs for email ids: {ids}")
    vsos = {}
    summaries = summarize_emails(ids)
    for sum_list in summaries:
        for summary in sum_list:
            print(summary)
            activity_id = summary["RowKey"]
            email_id = summary["EmailId"]
            vso_id = get_or_create_vsos(activity_id)
            if email_id not in vsos:
                vsos[email_id] = []
            vsos[email_id].append(vso_id)
    return vsos


# Get email metadata for a time range
@app.route('/ids', methods=['GET'])
def get_email_metadata():
    start = request.args.get('start', default='').replace("'", "")
    end = request.args.get('end', default='').replace("'", "")

    # Check if start or end parameters are missing and set default values
    if not start:
        start = (datetime.now(pytz.utc) - timedelta(hours=1)).isoformat()
    if not end:
        end = datetime.now(pytz.utc).isoformat()

    # Call the function to get emails by time range
    return emails_by_time_range(start, end)

# Get email ids between a start and end time as a list of strings
@app.route('/justids', methods=['GET'])
def get_id_list():
    start = request.args.get('start', default='').replace("'", "")
    end = request.args.get('end', default='').replace("'", "")

    if not start:
        start = (datetime.now(pytz.utc) - timedelta(hours=1)).isoformat()
    if not end:
        end = datetime.now(pytz.utc).isoformat()

    email_dict = emails_by_time_range(start, end)
    return ",".join([f"'{id}'" for id in email_dict])

# Get summaries for emails received within a time frame
# Generate new ones if they don't exist, otherwise retrieve cached ones
@app.route('/summaries', methods=['GET'])
def generate_summaries_by_time_range():
    start = request.args.get('start', default='').replace("'", "")
    end = request.args.get('end', default='').replace("'", "")

    return summarize_emails_in_range(start, end)

# Generate new summary and upload it regardless of if one exists already
# Don't catch errors so we can see full stack trace
@app.route('/summarizeforce', methods=['GET'])
def get_email_summary_force():
    ids = request.args.get('ids', default='').split(',')

    summaries = []
    for id in ids:
        clean_id = id.replace("'", "")
        print(f"Summarizing email {clean_id}")
        
        print(f"Writing new summary")
        email_body_blob = get_blob_client(STORAGE_CONNECTION_STRING, 'emails', clean_id)
        email_body_text = parse_html_blob(email_body_blob)
        print(f"Email body retrieved")
        summary = summarize_email(email_body_text)
        summaries.append(summary)
        print(f"Summary generated")

        upload_email_summary(summary, clean_id)
        print(f"Summary uploaded")
    return summaries

# Summarize emails specified by IDs. Don't generate a new summary if one exists already
@app.route('/summarize', methods=['GET'])
def get_email_summary():
    ids = request.args.get('ids', default='').split(',')
    return summarize_emails(ids)

# Takes email IDs and creates VSOs for them if they don't already have them
@app.route('/emailstovsos', methods=['GET'])
def email_ids_to_vso_ids():
    email_ids = request.args.get('ids', default='').replace("'", "").split(",")
    return get_vso_ids_for_emails(email_ids)

# Get or create VSOs for the given summary IDs, which are created on summary generation
# and used as the RowKey/PartitionKey in table storage for that summary
@app.route('/createvsos', methods=['GET'])
def create_vsos_by_activity_id():
    activity_ids = request.args.get('ids', default='').replace("'", "").split(",")

    vso_ids = []
    for id in activity_ids:
        vso_ids.append(get_or_create_vsos(id))

    return vso_ids

# # Automatically create summaries every few minutes from new emails in table storage
# auto_summaries = threading.Thread(target=generate_summaries_periodically)
# auto_summaries.daemon = True
# auto_summaries.start()

# # Automatically create VSOs from new summaries in table storage every few minutes
# auto_summaries = threading.Thread(target=generate_vsos_periodically)
# auto_summaries.daemon = True
# auto_summaries.start()

if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True, debug=True, port=80, host="0.0.0.0")