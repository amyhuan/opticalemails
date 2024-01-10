import os
from openai import AzureOpenAI
import dotenv
import sys
from model_specs import *
from datetime import datetime

dotenv.load_dotenv()

gpt_client = AzureOpenAI(
    azure_endpoint=OPENAI_INSTANCE,
    api_key=os.getenv('API_KEY'),
    api_version=OPENAI_API_VERSION
)

# Function to find a file starting with a given ID (VSO ID)
def find_file_with_id(directory, file_id):
    for filename in os.listdir(directory):
        if filename.startswith(file_id):
            return os.path.join(directory, filename)
    return None

def extract_first_column(tsv_string):
    lines = tsv_string.strip().split('\n')
    first_column_values = [line.split('\t')[0] for line in lines[1:] if line]
    return ' '.join(first_column_values)

# Summarize each email text
def process_file_content(content):
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
    id_list = extract_first_column(whole_output)
    return id_list

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

# Replace actual IDs column with current model results
def process_tsv(input_tsv, output_tsv, directory):
    existing_ids = get_existing_ids(output_tsv)

    with open(input_tsv, 'r', encoding='utf-8') as infile:
        infile_len = sum(1 for _ in infile)

    with open(input_tsv, 'r', encoding='utf-8') as infile, open(output_tsv, 'a', encoding='utf-8') as outfile:
        new_tests = 0
        for current_line, line in enumerate(infile):
            columns = line.strip().split('\t')
            if len(columns) >= 3:
                file_id = columns[0]

                # Skip processing if ID already exists in output file
                if file_id in existing_ids:
                    continue

                file_path = find_file_with_id(directory, file_id)
                if file_path:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_content = file.read()
                        output_string = process_file_content(file_content)
                        columns[2] = output_string
                outfile.write('\t'.join(columns) + '\n')
                outfile.flush()

                new_tests += 1
                if new_tests == 10:
                    calculate_success_rate(current_line, infile_len, output_tsv)
                    new_tests = 0

        print("Done processing VSO descriptions (maintenance email texts)")
        calculate_success_rate(infile_len, infile_len, output_tsv, True)

def record_test_results(percentage, incorrect_ids):
    with open("test/circuit_id_accuracy_results_summary.tsv", 'w', encoding='utf-8') as summary_file:
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

{percentage:.2f}% exact ID list match




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
            incorrect_ids_table = ""

            for line in outfile:
                total_rows += 1
                parts = line.strip().split('\t')
                if len(parts) < 3:
                    # print(f"only found 2 columns instead of 3: {line}")
                    continue
                if parts[0] == "VsoId":
                    continue

                vso_id, expected_ids, actual_ids = line.strip().split('\t')

                # Converting IDs from string to sets for easy comparison
                expected_ids_set = set(expected_ids.split())
                actual_ids_set = set(actual_ids.split())

                row_add = 1
                for expected in expected_ids_set:
                    if expected not in actual_ids_set:
                        # print(f"Missed an expected ID. VsoId: {vso_id}, Expected: {expected_ids}, Actual: {actual_ids}")
                        row_add = 0
                        incorrect_ids_table += f"""
VSO ID:         {vso_id}
Expected IDs:   {expected_ids}
Actual IDs:     {actual_ids}
"""

                # if len(actual_ids_set) > len(expected_ids_set):
                #     print(f"Included extra ID. VsoId: {vso_id}, Expected: {expected_ids}, Actual: {actual_ids}")

                matching_rows += row_add

            success_rate = (matching_rows / total_rows) * 100 if total_rows > 0 else 0
            sucess_rate_str = f"{current_line}/{input_len} input lines processed. Circuit ID Exact Match Rate: {success_rate:.2f}%"
            print(sucess_rate_str)

            if record_results:
                record_test_results(success_rate, incorrect_ids_table)

    except Exception as e:
        raise e 
    
input_tsv = 'test/circuit_id_accuracy_base_template.tsv'
output_tsv = 'test/circuit_id_accuracy_results.tsv'
directory = 'test/vso_descriptions' 

process_tsv(input_tsv, output_tsv, directory)
