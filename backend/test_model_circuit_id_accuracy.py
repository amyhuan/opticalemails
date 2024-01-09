import os
from openai import AzureOpenAI
import dotenv
from model_specs import *

dotenv.load_dotenv()

gpt_client = AzureOpenAI(
    azure_endpoint=OPENAI_INSTANCE,
    api_key=os.getenv('API_KEY'),
    api_version=OPENAI_API_VERSION
)

# Function to find a file starting with a given ID
def find_file_with_id(directory, file_id):
    for filename in os.listdir(directory):
        if filename.startswith(file_id):
            return os.path.join(directory, filename)
    return None

def extract_first_column(tsv_string):
    lines = tsv_string.strip().split('\n')
    first_column_values = [line.split('\t')[0] for line in lines[1:] if line]
    return ' '.join(first_column_values)

# Function to process file content (add your code here)
def process_file_content(content):
    # Add your processing code here
    # For example, just return the content for now
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

# Replace the third column in each row of the TSV
def process_tsv(input_tsv, output_tsv, directory):
    with open(input_tsv, 'r', encoding='utf-8') as infile, open(output_tsv, 'w', encoding='utf-8') as outfile:
        for line in infile:
            columns = line.strip().split('\t')
            if len(columns) >= 3:
                file_id = columns[0]
                file_path = find_file_with_id(directory, file_id)
                if file_path:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_content = file.read()
                        output_string = process_file_content(file_content)
                        columns[2] = output_string
                outfile.write('\t'.join(columns) + '\n')
                outfile.flush()

# Example usage
input_tsv = 'expected_vs_actual_circuit_ids_per_vso.tsv'  # Replace with your input TSV file path
output_tsv = 'new_expected_vs_actual_circuit_ids_per_vso.tsv' # Replace with your desired output TSV file path
directory = 'test/vso_descriptions'  # Replace with the directory containing the files

process_tsv(input_tsv, output_tsv, directory)
