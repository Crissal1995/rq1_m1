import pathlib
import logging

from src.major.generate_live_mutants import get_live_mutants, get_directory
from src.major.get_coupled_mutants import get_mutants_from_set, create_set_mutants
from src.utility import get_root_dir

"""
major scheme for mutation (mutants.log)

mutant_id, mutant_operator, original, mutation, function, line, full_mutation
    0              1             2        3          4      5         6
"""
ID = 0
OPERATOR = 1
ORIGINAL = 2
MUTATION = 3
FUNCTION = 4
LINE = 5
FULL_MUTATION = 6


FORMAT_VERBOSE = "%(levelname)s::%(module)s::%(lineno)d::%(asctime)s::%(message)s"
FORMAT = "%(levelname)s...%(asctime)s...%(message)s"

logging.basicConfig(filename="major.log", format=FORMAT, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("---NEW EXECUTION---")

root_dir = get_root_dir("cli", "major")

buggy_dir = root_dir / "buggy"
fixed_dir = root_dir / "fixed"
fname = "generated_live_mutants.log"

buggy_mutants = get_live_mutants(buggy_dir)
fixed_mutants = get_live_mutants(fixed_dir)

set_keys = (
    LINE,
    OPERATOR,
    ORIGINAL,
    MUTATION,
    FULL_MUTATION
)
buggy_set = create_set_mutants(buggy_mutants, set_keys)
fixed_set = create_set_mutants(fixed_mutants, set_keys)
diff_set = buggy_set - fixed_set

diff_mutants = get_mutants_from_set(buggy_mutants, diff_set, set_keys, sort_on=ID)

logging.info(f"Caught {len(diff_set)} mutants in the diff set")

with open(root_dir / "diffset.log", "w") as f:
    f.writelines("...".join(mutant) + "\n" for mutant in diff_mutants)
