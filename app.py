from datetime import datetime
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

dotenv.load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app)

client = AzureOpenAI(
    azure_endpoint="https://amyhuan-openai.openai.azure.com",
    api_key=os.getenv('API_KEY'),
    api_version="2023-07-01-preview"
)

STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')

def query_table_by_timestamp(connection_string, table_name, start_time, end_time):
    """
    Queries an Azure Table for rows where the Timestamp is between start_time and end_time.

    :param connection_string: Connection string to the Azure Table storage account.
    :param table_name: Name of the table.
    :param start_time: Start of the time range (inclusive), in ISO 8601 format.
    :param end_time: End of the time range (inclusive), in ISO 8601 format.
    :return: List of entities matching the time range.
    """
    table_service_client = TableServiceClient.from_connection_string(conn_str=connection_string)
    table_client = table_service_client.get_table_client(table_name=table_name)

    query_filter = f"TimeReceived ge '{start_time}' and TimeReceived le '{end_time}'"
    entities = table_client.query_entities(query_filter)

    return list(entities)

def email_ids_by_time_range(start_time, end_time):
    entities = query_table_by_timestamp(STORAGE_CONNECTION_STRING, "maintenances", start_time, end_time)
    row_keys = [entity['RowKey'] for entity in entities]

    print(f"Email IDs: {row_keys}")
    return row_keys

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

@app.route('/emailids', methods=['GET'])
def get_email_ids():
    # start_timestamp = request.args.get('startTime', default='').replace('\'', '')
    # end_timestamp = request.args.get('endTime', default='').replace('\'', '')
    start_time = "2023-11-20T20:02:26+00:00"
    end_time = "2023-11-22T20:02:26+00:00"
    return email_ids_by_time_range(start_time, end_time)

@app.route('/emailsummaries', methods=['GET'])
def get_email_summaries():
    start_time = "2023-11-20T20:02:26+00:00"
    end_time = "2023-11-22T20:02:26+00:00"

    ids = email_ids_by_time_range(start_time, end_time)
    summaries = []
    for id in ids:
        try:
            blob_client = get_blob_client(STORAGE_CONNECTION_STRING, 'emails', id)
            text = parse_html_blob(blob_client)

            res = client.chat.completions.create(
                model="vscode-gpt",
                messages=[
                    {"role": "system", "content": "Each message you will get contains the contents of a fiber provider maintenance email, sometimes incomplete. Summarize the information by noting what kind of maintenance is happening and what specific circuit IDs are affected, where they are located, and for what time range. If the message does not contain this information, do not return any summary."},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                max_tokens=256
            )
            summaries.append(res.choices[0].message.content)
        except Exception as e:
            print(e)
            continue
    return summaries

@app.route('/', methods=['GET'])
def base_path():
    return jsonify("success")

if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True, debug=True, port=8080, host="0.0.0.0")