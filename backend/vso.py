import requests
import json
#use the library below to perform retry logic on the API call
#from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
import pprint
import os
import dotenv

dotenv.load_dotenv()
VSO_AUTH_TOKEN = os.getenv('VSO_AUTH_TOKEN')
CIRCUIT_INFO_API_KEY = os.getenv('CIRCUIT_INFO_API_KEY')

def get_devices_for_circuits(circuit_ids):
    for i in circuit_ids:
        api_call = 'https://opticaldatainformation.azurewebsites.net/api/opticaldatainformation?vendor_circuit_id=' + i + '&code=' + CIRCUIT_INFO_API_KEY
        try:
            #add retry logic
            response = requests.get(api_call)
            response.raise_for_status()
            data = json.loads(response.content)
            if data['source'] == 'None' and data['circuit_details']:
                #Create a sev 3 for no data for Kaitlyn.
                print(data)
                print('No data found for circuit ' + i)
            else:
                data = json.loads(response.content)
                device_list = []
                if data['additional_info']:
                    for device in data['additional_info'][1]:
                        device_list.append(device['StartDevice'])
                        device_list.append(device['EndDevice'])
                    print(device_list)
                elif 'device_records_exist' in data:
                    for i in data['circuit_details']:
                        if 'OpticalDeviceA' in i and 'OpticalDeviceZ' in i:
                            device_list.append(i['OpticalDeviceA'])
                            device_list.append(i['OpticalDeviceZ'])
                        elif 'DeviceName' in i:
                            device_list.append(i['DeviceName'])
                        else:
                            print(data['circuit_details'])
                    if device_list:
                        return device_list
                else:
                    print(json.loads(response.content))
        except requests.exceptions.HTTPError as e:
            print('Error: ' + str(e))
            print('No data found for circuits ' + circuit_ids)

    return []

def get_msazure_teams():
    organization = 'https://dev.azure.com/msazure'
    #project = 
    #type = 
    #(device_list, start_time, end_time)
    #, auth=('', token)
    credentials = BasicAuthentication('', VSO_AUTH_TOKEN)
    connection = Connection(base_url=organization, creds=credentials)
    # Get a client (the "core" client provides access to projects, teams, etc)
    core_client = connection.clients.get_core_client()
    get_projects_response = core_client.get_projects()
    index = 0
    while get_projects_response is not None:
        if hasattr(get_projects_response, 'value'):
            projects = get_projects_response.value
            continuation_token = get_projects_response.continuation_token
        else:
            # get_projects_response is a list
            projects = get_projects_response
            continuation_token = None

        for project in projects:
            pprint.pprint("[" + str(index) + "] " + project.name)
            index += 1

        if continuation_token is not None and continuation_token != "":
            get_projects_response = core_client.get_projects(continuation_token=continuation_token)
        else:
            get_projects_response = None
            
def get_vso_info():
    project = 'PhyNet'
    id = 24599773
    organization = 'https://dev.azure.com/msazure'
    credentials = BasicAuthentication('', VSO_AUTH_TOKEN)
    connection = Connection(base_url=organization, creds=credentials)
    # Get a client (the "core" client provides access to projects, teams, etc)
    wit_client = connection.clients.get_work_item_tracking_client()
    work_item = wit_client.get_work_item(id, expand='all')
    soup_devices = BeautifulSoup(work_item.fields['PhyNet.Devices'], 'html.parser')
    text_devices = soup_devices.get_text(separator=', ').strip()
    print(text_devices)
    print(work_item.fields['Microsoft.VSTS.CMMI.ImpactAssessmentHtml'])
    print( work_item.fields['System.AreaPath']) 
    soup_description = BeautifulSoup(work_item.fields['System.Description'], 'html.parser')
    text_description = soup_description.get_text(separator=', ').strip()
    print(text_description)
    print(work_item.fields['System.Title'])
    print(work_item.fields['System.WorkItemType'])
    print(work_item.fields['System.State'])
    print(work_item.fields['System.CreatedDate'])
    print(work_item.fields['System.ChangedDate'])
    print(work_item.fields['System.CreatedBy']['displayName'])
    print(work_item.fields['System.ChangedBy']['displayName'])
    print(work_item.fields['System.Tags'])
    print(work_item.fields['System.IterationPath'])
    print(work_item.fields['System.AreaPath'])
    print(work_item.fields['System.TeamProject'])
    print(work_item.fields['System.Id'])
    print(work_item.fields['Microsoft.VSTS.Scheduling.FinishDate'])
    print(work_item.fields['Microsoft.VSTS.Scheduling.StartDate'])
    print(work_item.fields['System.AssignedTo'])

def create_vso_ticket(title, description, work_item_type, project, circuits, phynet_devices, start_time, end_time, location):
    organization = 'https://dev.azure.com/msazure'
    credentials = BasicAuthentication('', VSO_AUTH_TOKEN)
    connection = Connection(base_url=organization, creds=credentials)
    wit_client = connection.clients.get_work_item_tracking_client()
    document = [
        JsonPatchOperation(op="add", path="/fields/System.Title", value=f"[TEST] {title}"),
        JsonPatchOperation(op="add", path="/fields/System.Description", value=description),
        JsonPatchOperation(op="add", path="/fields/System.WorkItemType", value=work_item_type),
        JsonPatchOperation(op="add", path="/fields/System.TeamProject", value=project),
        JsonPatchOperation(op="add", path="/fields/Microsoft.VSTS.Common.Risk", value="2 - Medium"),
        JsonPatchOperation(op="add", path="/fields/System.AreaPath", value="PhyNet\\WANChanges"),
        JsonPatchOperation(op="add", path="/fields/PhyNet.Devices", value=phynet_devices),
        JsonPatchOperation(op="add", path="/fields/PhyNet.Circuits", value=circuits),
        JsonPatchOperation(op="add", path="/fields/PhyNet.Datacenter", value=location),
        JsonPatchOperation(op="add", path="/fields/Microsoft.VSTS.Scheduling.StartDate", value=start_time),
        JsonPatchOperation(op="add", path="/fields/Microsoft.VSTS.Scheduling.FinishDate", value=end_time),
        JsonPatchOperation(op="add", path="/fields/System.AssignedTo", value="amyhuan@microsoft.com"),
    ]
    work_item = wit_client.create_work_item(document=document, project=project, type=work_item_type)
    return work_item

def create_new_maintenance_vso(provider, start_time, end_time, circuit_ids, phynet_devices, description, location):
    project = 'PhyNet'
    work_item_type = 'Change Record'  
    title = f"{provider} maintenance for circuits {', '.join(circuit_ids)}"
    new_work_item = create_vso_ticket(title, description, work_item_type, project, ", ".join(circuit_ids), ", ".join(phynet_devices), start_time, end_time, location)
    return new_work_item

def send_vso_information():
    project = 'PhyNet'
    work_item_type = 'Change Record'  
    title = 'Srinivas Test Ticket'
    description = 'This is a sample description for the work item.'
    start_time = 'This is a sample description for the work item.'
    end_time = 'This is a sample description for the work item.'
    phynet_devices = ['ear06.mrs20', 'mil30-96cbe-1b', 'ear05.mrs20', 'mil30-96cbe-1a']
    phynet_devices_string = ', '.join(phynet_devices)

    new_work_item = create_vso_ticket(title, description, work_item_type, project, phynet_devices_string, start_time, end_time)
    print("Created new work item with ID:", new_work_item.id)

def test_vso_creation():
    new_vso = create_new_maintenance_vso("ProviderName", 
                                         "2023-07-20T09:27:08.253Z", 
                                         "2023-07-25T03:15:53.947Z",
                                         ['CircuitName1', 'CircuitName2', 'CircuitName3'],
                                         ['ear06.mrs20', 'mil30-96cbe-1b', 'ear05.mrs20', 'mil30-96cbe-1a'],
                                         "Email Metadata and Body text here. New maintenance scheduled by provider.",
                                         "GeographicLocation")
    print(new_vso)

if __name__ == '__main__':
    test_ids = ['MSFT-CH1B-DM5B-MSCG-0019-0::100GBE-1', 'XBG/MRS/LE-268957', 'NVADF052-Span26-002', 'mnz20-bl7-iad069-west-01osp', 'NVADF052-21/22', 'MICR2-AKMH', 'NVADF052-Span129-001', 'F19M-0097756_017-018']
    # devices_for_test_ids = get_devices_for_circuits(test_ids)
    # print(devices_for_test_ids)
    # get_vso_info()
    test_vso_creation()