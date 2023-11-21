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

dotenv.load_dotenv()
app = Flask(__name__)

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

@app.route('/emailids', methods=['GET'])
def get_email_ids():
    start_timestamp = request.args.get('startTime', default='').replace('\'', '')
    end_timestamp = request.args.get('endTime', default='').replace('\'', '')

    table_name = "maintenances"
    start_time = "2023-11-10T00:00:00Z"
    end_time = "2023-11-15T00:00:00Z"
    entities = query_table_by_timestamp(STORAGE_CONNECTION_STRING, table_name, start_time, end_time)
    row_keys = extract_row_keys(entities)

    print(f"Email IDs: {row_keys}")
    return row_keys

@app.route('/emailsummaries', methods=['GET'])
def get_email_summaries():
    ids = [] # TODO: get ids with api call
    summaries = []
    for id in ids:
        try:
            blob_client = get_blob_client(STORAGE_CONNECTION_STRING, 'emails', id)
            text = parse_html_blob(blob_client)
            emit('message', f"Email text: \n {text}")

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
        except e:
            print(e)
            continue
    return summaries

@app.route('/', methods=['GET'])
def base_path():
    return jsonify("success")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)