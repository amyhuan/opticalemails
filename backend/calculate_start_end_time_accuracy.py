import os
from datetime import datetime
import csv

# read TSV of expected start and end times
def read_expected_times(file_path):
    expected_times = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        next(file)  # Skip header
        for line in file:
            columns = line.strip().split('\t')
            if len(columns) == 3:
                vso_id = columns[0]
                start_time = datetime.strptime(columns[1], '%Y-%m-%dT%H:%M:%SZ')
                end_time = datetime.strptime(columns[2], '%Y-%m-%dT%H:%M:%SZ')
                expected_times[vso_id] = (start_time, end_time)
    return expected_times

def process_email_summaries(directory, expected_times):
    total_files = 0
    matched_files = 0

    for filename in os.listdir(directory):
        vso_id, _ = os.path.splitext(filename)
        if vso_id in expected_times:
            total_files += 1
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter='\t')
        
                for row in reader:
                    if "StartDatetime" in row and "EndDatetime" in row and row["StartDatetime"] and row["EndDatetime"]:
                        start_times = row["StartDatetime"].split(",")
                        end_times = row["EndDatetime"].split(",")
                        for s, e in zip(start_times, end_times):
                            try:
                                start_time = datetime.strptime(s.strip(), '%Y-%m-%d %H:%M')
                                end_time = datetime.strptime(e.strip(), '%Y-%m-%d %H:%M')
                                if (start_time, end_time) == expected_times[vso_id]:
                                    matched_files += 1
                                    break  # Process only the first line of each file
                            except Exception as e:
                                print(f"{vso_id}: {e}")

    return total_files, matched_files

def calculate_match_percentage(total_files, matched_files):
    print(f"matched: {matched_files} total: {total_files}")
    if total_files == 0:
        return 0
    return (matched_files / total_files) * 100

# Main execution
expected_start_end_file = 'test/start_end_times/expected_start_end_times.tsv'
email_summaries_directory = 'test/email_summaries'

expected_times = read_expected_times(expected_start_end_file)
total_files, matched_files = process_email_summaries(email_summaries_directory, expected_times)
percentage_match = calculate_match_percentage(total_files, matched_files)

print(f"Percentage of time matches: {percentage_match:.2f}%")
