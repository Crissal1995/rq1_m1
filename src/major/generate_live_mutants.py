import csv
import pathlib
import logging

# change subject and version (via fixed)
subjects = {'cli': 'cli32', 'lang': 'lang53', 'gson': 'gson15'}


def get_directory(home, subject, version=None):
    assert version in (None, "buggy", "fixed")
    assert subject in subjects.values()

    logging.info(f"Subject: {subject}")
    logging.info(f"Version: {version}")

    p = pathlib.Path(home) / f"data/{subject}/major"
    if version:
        p = p / f"{version}"
    return p


def get_live_mutants(directory):
    kill_fp = directory / 'kill.csv'
    mutants_fp = directory / 'mutants.log'

    with open(kill_fp) as f:
        reader = csv.reader(f)
        live_mutants_id = [mutant_id for mutant_id, status in reader if status == "LIVE"]
        logging.info(f"{live_mutants_id=}")

    with open(mutants_fp) as f:
        reader = csv.reader(f, delimiter=":")
        rows = []
        for row in reader:
            clean_row = row[:7]
            if len(row) > 7:
                clean_row[6] = ':'.join(row[6:])
            rows.append(clean_row)

        """
        mutants = [
            (mutant_id, mutant_operator, original, mutation, function, line, full_mutation)
            for mutant_id, mutant_operator, original, mutation, function, line, full_mutation in rows
                   0              1             2        3          4       5         6
        ]
        """
        live_mutants = [mutant for mutant in rows if mutant[0] in live_mutants_id]
        logging.info(f"{live_mutants=}")

    live_mutants_fp = directory / 'generated_live_mutants.log'
    with open(live_mutants_fp, 'w') as f:
        f.writelines("...".join(mutant) + "\n" for mutant in live_mutants)

    return live_mutants
