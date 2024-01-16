import os
from openai import AzureOpenAI
import dotenv
import sys
from model_specs import *
from datetime import datetime
import threading
from queue import Queue

dotenv.load_dotenv()

gpt_client = AzureOpenAI(
    azure_endpoint=OPENAI_INSTANCE,
    api_key=os.getenv('API_KEY'),
    api_version=OPENAI_API_VERSION
)

input_tsv = 'test/start_end_times/expected_start_end_times.tsv'
output_tsv = 'test/start_end_times/start_end_times_accuracy_results.tsv'
summary_tsv = 'test/start_end_times/start_end_times_accuracy_results_summary.tsv'
emails_dir = 'test/vso_descriptions' 


# Function to find a file starting with a given ID (VSO ID)
def find_file_with_id(directory, file_id):
    for filename in os.listdir(directory):
        if filename.startswith(file_id):
            return os.path.join(directory, filename)
    return None

def extract_start_end_times(tsv_string):
    lines = tsv_string.strip().split('\n')
    start_times = [line.split('\t')[1] for line in lines[1:] if line]
    end_times = [line.split('\t')[2] for line in lines[1:] if line]
    return ' '.join(start_times), ' '.join(end_times)

# Summarize each email text
def process_file_content(vso_id, content):
    try:
        res = gpt_client.chat.completions.create(
                model=MODEL_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
        whole_output = res.choices[0].message.content
        starts, ends = extract_start_end_times(whole_output)
    except Exception as e:
        print(f"Failed to summarize {vso_id}")
        return "", ""
    return starts, ends

# Get VSO IDs that are already processed
def get_existing_ids(file_name):
        existing_ids = {}
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                for line in file:
                    id = line.split('\t')[0]
                    existing_ids[id] = True
        except FileNotFoundError:
            pass
        return existing_ids

def process_line(columns, directory, output_queue):
    vso_id = columns[0]
    file_path = find_file_with_id(directory, vso_id)
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            extracted_start, extracted_end = process_file_content(vso_id, file_content)
        old_cols = "\t".join(columns)
        output_queue.put(f"{old_cols}\t{extracted_start}\t{extracted_end}")

def worker(input_queue, output_queue, directory):
    while True:
        columns = input_queue.get()
        if columns is None:
            input_queue.task_done()
            break
        process_line(columns, directory, output_queue)
        input_queue.task_done()

def process_tsv(input_tsv, output_tsv, emails_dir):
    existing_ids = get_existing_ids(output_tsv)
    input_queue = Queue()
    output_queue = Queue()
    num_worker_threads = 40

    threads = []
    for i in range(num_worker_threads):
        t = threading.Thread(target=worker, args=(input_queue, output_queue, emails_dir))
        t.start()
        threads.append(t)

    with open(input_tsv, 'r', encoding='utf-8') as infile, open(output_tsv, 'a', encoding='utf-8') as outfile:
        infile_len = sum(1 for _ in infile)
        infile.seek(0)

        new_tests = 0
        for current_line, line in enumerate(infile):
            columns = line.strip().split('\t')
            if len(columns) >= 3 and columns[0] not in existing_ids:
                input_queue.put(columns)
                new_tests += 1
                if new_tests == 15:
                    input_queue.join()
                    while not output_queue.empty():
                        outfile.write(output_queue.get())
                    print(f"{current_line}/{infile_len} input lines processed")
                    new_tests = 0

        # Stop workers
        for i in range(num_worker_threads):
            input_queue.put(None)
        for t in threads:
            t.join()
        print("stopped workers")

        input_queue.join()
        print("joined input")
        while not output_queue.empty():
            outfile.write(output_queue.get())
        print("wrote output")
        
        print("Done processing VSO descriptions (maintenance email texts)")
        calculate_success_rate(infile_len, infile_len, output_tsv, True)

def record_test_results(percentage, incorrect_ids, current_line, input_len):
    with open(summary_tsv, 'w', encoding='utf-8') as summary_file:
        summary = f"""
Circuit ID accuracy test - ask GPT to summarize emails taken from VSO descriptions and compare the IDs extracted compared to the actual
IDs included in the VSO

Date and time run:      {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Pacific Time
OpenAI Instance:        {OPENAI_INSTANCE}
OpenAI API Version:     {OPENAI_API_VERSION}
Model deployment name:  {MODEL_DEPLOYMENT}
Temperature:            {TEMPERATURE}
Max Tokens:             {MAX_TOKENS}

Model system prompt:    {SYSTEM_PROMPT}

{current_line} out of {input_len} input VSOs processed. {percentage:.2f}% exact ID list match




Incorrect ID extractions:
{incorrect_ids}
        """
        summary_file.write(summary)

# calculate success rate based on if the actual IDs match the expected IDs
def calculate_success_rate(current_line, input_len, output_tsv, record_results=False):
    try:
        with open(output_tsv, 'r', encoding='utf-8') as outfile:
            total_rows = 0
            matching_rows = 0
            incorrect_table = ""

            for line in outfile:
                total_rows += 1
                parts = line.strip().split('\t')
                if parts[0] == "VsoId":
                    continue

                vso_id, expected_start, expected_end, actual_start, actual_end = line.strip().split('\t')

                if expected_start != actual_start or expected_end != actual_end:
                    incorrect_table += f"""
VSO ID:         {vso_id}
Expected Start: {expected_start}
Actual Start:   {actual_start}
Expected End:   {expected_end}
Actual End:     {actual_end}                    
"""
                else:
                    matching_rows += 1

            success_rate = (matching_rows / total_rows) * 100 if total_rows > 0 else 0
            sucess_rate_str = f"{current_line}/{input_len} input lines processed. Circuit ID Exact Match Rate: {success_rate:.2f}%"
            print(sucess_rate_str)

            if record_results:
                record_test_results(success_rate, incorrect_table, current_line, input_len)

    except Exception as e:
        raise e 

print(process_file_content("16694439", """Dear Equinix Customer,



DATE: 26-JAN-2023 - 27-JAN-2023



SPAN: 26-JAN-2023 - 27-JAN-2023



LOCAL: THURSDAY, 26 JAN 22:00 - FRIDAY, 27 JAN 06:00

UTC: THURSDAY, 26 JAN 14:00 - THURSDAY, 26 JAN 22:00



IBX(s): HK1,HK2,HK3,HK4,HK5,HP1



DESCRIPTION:Please be advised that Equinix engineers identified a software bug and will perform a software upgrade on our Metro Connect devices.



During the maintenance, the following impact are expected depending on your subscribed service:



1. Unprotected Metro Connect circuits will experience service interruption of up to 60 minutes.



2. Protected Metro Connect circuits will experience service interruption of up to 60 minutes.



3. One of your Dual Diverse Metro Connect circuits will experience port downtime of up to 60 minutes but no service interruption due to redundancy.



4. Equinix Fabric Metro Remote Port will experience service interruption of up to 60 minutes. If you have secondary circuit, please ensure to have redundant VC to avoid service interruption.



5. Equinix Connect Single Homed customers will experience service interruption of up to 60 minutes



6. Network Edge circuits will experience service interruption of up to 60 minutes. If you have secondary circuit, please ensure to have redundant VC to avoid service interruption.



PRODUCTS: EQUINIX FABRIC, METRO CONNECT, NETWORK EDGE



IMPACT: There will be service interruptions.





Equinix Fabric



Account #	Product	IBX	Service Serial #	ECX Port	L2 Seller Profile Name	L2 Connection Name	L2 Connection UUID	L3 Seller Profile Name	L3 Subscription Name	L3 Subscription UUID	Virtual Asset Type	Virtual Asset Name	Virtual Asset UUID

116771	Equinix Fabric	HK1	20500763-A	-	-	-	-	-	-	-	-	-	-







We apologize for any inconvenience you may experience during this activity. Your cooperation and understanding are greatly appreciated.



The Equinix SMC is available to provide up-to-date status information or additional details, should you have any questions regarding the maintenance. Please reference 5-222102819313.



Sincerely,

Equinix SMC"""))
process_tsv(input_tsv, output_tsv, emails_dir)
