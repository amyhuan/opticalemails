def parse_line_to_tsv(line):
    """
    Parses a given line from the file and converts it into a TSV format.
    Assumes the line is in the format:
    "Comparing <VsoId>: ['<ExpectedId1>', '<ExpectedId2>', ...] vs ['<ActualId1>', '<ActualId2>', ...]"

    Returns a string in TSV format.
    """
    try:
        # Splitting the line to extract the necessary parts
        parts = line.split(": ")
        space_parts = line.split()
        vso_id = space_parts[1].replace(":", "")  # Extracting VsoId

        # Extracting the list of ExpectedIds
        expected_ids_list = parts[1].split("[")[1].split("]")[0].replace("'", "").replace("\"", "").split(", ")

        # Extracting the list of ActualIds
        actual_ids_list = parts[1].split("[")[2].split("]")[0].replace("'", "").replace("\"", "").split(", ")

        # Creating a TSV line
        tsv_line = f"{vso_id}\t{' '.join(expected_ids_list)}\t{' '.join(actual_ids_list)}\n"
        return tsv_line
    except Exception as e:
        print(f"Exception: {e} at line {line}")
    return ""

def convert_file_to_tsv(input_file, output_file):
    """
    Reads a file with specific formatted lines, parses each line,
    and writes the result in TSV format to an output file.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        # Writing headers
        outfile.write("VsoId\tExpectedIds\tActualIds\n")

        # Reading and parsing each line
        for line in infile:
            tsv_line = parse_line_to_tsv(line)
            outfile.write(tsv_line)

# Example usage
input_file = "input_test_results.txt"  # Replace with the actual file path
output_file = "expected_vs_actual_circuit_ids_per_vso.tsv"  # The output file path
convert_file_to_tsv(input_file, output_file)