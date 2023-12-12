from datetime import datetime, timedelta
import pytz
from flask import Flask, request, jsonify
import json
from typing import Dict
from flask_cors import CORS
import dotenv
import requests
import time
from azure.storage.blob import BlobServiceClient
import os
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient
from openai import AzureOpenAI
from flask_socketio import SocketIO, send, emit
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import uuid
from azure.data.tables import TableEntity

dotenv.load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000", 
    "https://auto-vso.azurewebsites.net"
]}})
socketio = SocketIO(app)

gpt_client = AzureOpenAI(
    azure_endpoint="https://amyhuan-openai.openai.azure.com",
    api_key=os.getenv('API_KEY'),
    api_version="2023-07-01-preview"
)

STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')
AZURE_TABLES_CLIENT = table_service_client = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
EMAIL_METADATA_TABLE_CLIENT = table_service_client.get_table_client(table_name='MaintenanceEmailMetadata')
MAINTENANCE_TABLE_CLIENT = table_service_client.get_table_client(table_name='MaintenanceDetails')

EMAIL_SUMMARY_HEADERS = ['CircuitIds', 'StartDatetime', 'EndDatetime', 'NotificationType', 'MaintenanceReason', 'GeographicLocation', 'VsoId']

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

def parse_html_blob(blob_client):
    """
    Parses an HTML blob and returns the text of each tag.
    """
    # Download the blob content
    blob_data = blob_client.download_blob().readall()
    html_content = blob_data.decode('utf-8')

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text from specific tags (e.g., body)
    body_text = soup.body.get_text(strip=True) if soup.body else None

    return body_text

def summarize_email(email_html):
    res = gpt_client.chat.completions.create(
            model="vscode-gpt",
            messages=[
                {"role": "system", "content": """Each message you will get contains the contents of a fiber provider maintenance email update. 
                Return a TSV summarizing the maintenances mentioned with the following header column names. Each distinct maintenance should have exactly
                one start time and end time, and have its own row in the TSV. Include every header even if there are no associated values for it.
                1) CircuitIds - Fiber circuit IDs affected. Separate multiple IDs with newlines.
                2) StartDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm 
                3) EndDatetime - Date and time for start of maintenance, in UTC time in this 24 hour format: yyyy-mm-dd HH:mm 
                3) NotificationType - e.g. new maintenance scheduled, maintenance cancelled or postponed, or completed
                4) MaintenanceReason - Reason for maintenance if applicable
                5) GeographicLocation - Geographic location of the maintenance
                6) VsoId - If applicable, the Microsoft VSO ID that this maintenance is associated with
                
                Here is an example:
                CircuitIds\tStartDatetime\tEndDatetime NotificationType\tMaintenanceReason\tGeographicLocation\tVsoId\n
                OGYX/172340//ZYO,OQYX/376545//ZYO\t2023-11-07 07:01\t2023-12-07 07:01\tNew maintenance scheduled\tReplacing damaged fiber\tFresno CA\t15438446
                """},
                {"role": "user", "content": email_html},
            ],
            temperature=0,
            max_tokens=256
        )
    return res.choices[0].message.content

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

def summarize_emails(ids):
    all_summaries = []

    for id in ids:
        clean_id = id.replace("'", "")
        print(f"Summarizing email {clean_id}")

        query_filter = f"EmailId eq '{clean_id}'"
        entities = MAINTENANCE_TABLE_CLIENT.query_entities(query_filter)
        entity_list = [ent for ent in entities]

        if len(entity_list) > 0:
            print("Summary exists in table")
            # get summaries as list
            all_summaries.append(entity_list)
            continue
    
        print(f"Summary doesn't exist, creating new one now")
        email_body_blob = get_blob_client(STORAGE_CONNECTION_STRING, 'emails', clean_id)

        email_body_text = parse_html_blob(email_body_blob)
        print(f"Email body retrieved")

        summary_tsv = summarize_email(email_body_text)
        print(f"Summary generated")

        summaries = upload_email_summary(summary_tsv, clean_id)
        all_summaries.append(summaries)
        print(f"Summary uploaded")

    return all_summaries

# Summarize emails specified by IDs. Don't generate a new summary if one exists already
@app.route('/summarize', methods=['GET'])
def get_email_summary():
    ids = request.args.get('ids', default='').split(',')
    return summarize_emails(ids)

def upload_email_summary(summary, email_id):
    summaries = []

    try:
        rows = summary.split('\n')

        for row in rows[1:]:
            values = row.split("\t")
            if len(values) != len(EMAIL_SUMMARY_HEADERS):
                continue

            row_key = str(uuid.uuid4())
            new_entity = {}
            
            for i, header in enumerate(EMAIL_SUMMARY_HEADERS):
                new_entity[header] = values[i]

            new_entity["RowKey"] = row_key
            new_entity["PartitionKey"] = row_key
            new_entity["EmailId"] = email_id

            summaries.append(new_entity)
            MAINTENANCE_TABLE_CLIENT.create_entity(entity=TableEntity(**new_entity))
        
    except Exception as e:
        print(e)
        raise e

    return summaries

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

    email_dict = emails_by_time_range(start, end)
    ids = [f"'{id}'" for id in email_dict]

    return summarize_emails(ids)


if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True, debug=True, port=80, host="0.0.0.0")