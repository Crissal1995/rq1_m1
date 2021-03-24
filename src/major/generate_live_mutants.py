import csv
import pathlib
import logging

# file.py -> major dir -> src dir -> root dir
HOME = pathlib.Path(__file__).parent.parent.parent

FORMAT_VERBOSE = "%(levelname)s::%(module)s::%(lineno)d::%(asctime)s::%(message)s"
FORMAT = "%(levelname)s::%(message)s"

logging.basicConfig(filename="major.log", format=FORMAT, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("---NEW EXECUTION---")

# change subject and version (via fixed)
subjects = {'cli': 'cli32', 'lang': 'lang53', 'gson': 'gson15'}
_subject = subjects['cli']

fixed = True
_version = 'fixed' if fixed else 'buggy'


def get_directory(subject, version):
    assert version in ("buggy", "fixed")
    assert subject in subjects.values()

    logging.info(f"Subject: {subject}")
    logging.info(f"Version: {version}")

    return pathlib.Path(HOME) / f"data/{subject}/major/{version}"


_directory = get_directory(_subject, _version)


# start common code
def work_on_directory(directory=_directory):
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
        ]
        """
        live_mutants = [mutant for mutant in rows if mutant[0] in live_mutants_id]
        logging.info(f"{live_mutants=}")

    # store live mutants
    live_mutants_fp = directory / 'generated_live_mutants.log'
    with open(live_mutants_fp, 'w') as f:
        keys = [0, 1, 5, 3, 6]
        f.writelines("...".join([mutant[k] for k in keys]) + "\n" for mutant in live_mutants)

    return live_mutants


subject = subjects["cli"]

fixed_directory = get_directory(subject=subject, version="fixed")
fixed_live_mutants = work_on_directory(fixed_directory)

buggy_directory = get_directory(subject=subject, version="buggy")
buggy_live_mutants = work_on_directory(buggy_directory)
