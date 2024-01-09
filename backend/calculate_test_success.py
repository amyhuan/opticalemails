def calculate_success_rate(input_file):
    """
    Reads a TSV file with columns VsoId, ExpectedIds, and ActualIds.
    Calculates the percentage of rows where the ExpectedIds and ActualIds match.
    Prints the VsoId and both lists of IDs for rows where they don't match.
    Finally, prints the overall percentage success rate.
    """
    total_rows = 0
    matching_rows = 0

    with open(input_file, 'r') as infile:
        # Skipping the header
        next(infile)

        # Processing each row
        for line in infile:
            total_rows += 1
            vso_id, expected_ids, actual_ids = line.strip().split('\t')

            # Converting IDs from string to sets for easy comparison
            expected_ids_set = set(expected_ids.split())
            actual_ids_set = set(actual_ids.split())

            row_add = 1

            for expected in expected_ids_set:
                if expected not in actual_ids_set:
                    print(f"Missed an expected ID. VsoId: {vso_id}, Expected: {expected_ids}, Actual: {actual_ids}")
                    row_add = 0

            if len(actual_ids_set) > len(expected_ids_set):
                print(f"Included extra ID. VsoId: {vso_id}, Expected: {expected_ids}, Actual: {actual_ids}")

            matching_rows += row_add

    # Calculating the success rate
    success_rate = (matching_rows / total_rows) * 100 if total_rows > 0 else 0
    print(f"Success Rate: {success_rate:.2f}%")

# Example usage
input_file = "expected_vs_actual_circuit_ids_per_vso.tsv"
calculate_success_rate(input_file)
