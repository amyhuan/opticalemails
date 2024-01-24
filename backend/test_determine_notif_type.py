import csv
from app import *

def process_value(value):
    # Example function: doubles the value. Replace this with your actual function.
    return is_notification_type_new_maintenance(value)

def process_tsv(input_file, output_file):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile, delimiter='\t')
        writer = csv.writer(outfile, delimiter='\t')

        for row in reader:
            if row:  # check if row is not empty
                processed_value = process_value(row[0])
                row.append(processed_value)  # add the second column if it doesn't exist
                print(f"{row}")
                writer.writerow(row)

# Usage
input_tsv = 'test/notification_types.tsv'
output_tsv = 'test/notification_types_results.tsv'
process_tsv(input_tsv, output_tsv)