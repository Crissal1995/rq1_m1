import pathlib
import logging

from src.major.generate_live_mutants import get_live_mutants, get_directory
from src.major.get_coupled_mutants import get_mutants_from_set, create_set_mutants

FORMAT_VERBOSE = "%(levelname)s::%(module)s::%(lineno)d::%(asctime)s::%(message)s"
FORMAT = "%(levelname)s...%(asctime)s...%(message)s"

logging.basicConfig(filename="major.log", format=FORMAT, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("---NEW EXECUTION---")

# file.py -> major dir -> src dir -> root dir
HOME = pathlib.Path(__file__).parent.parent.parent

subjects = {'cli': 'cli32', 'lang': 'lang53', 'gson': 'gson15'}
subject = subjects["cli"]
root_dir = get_directory(HOME, subject)

buggy_dir = root_dir / "buggy"
fixed_dir = root_dir / "fixed"
fname = "generated_live_mutants.log"

buggy_mutants = get_live_mutants(buggy_dir)
fixed_mutants = get_live_mutants(fixed_dir)

set_keys = (1, 2, 4)
buggy_set = create_set_mutants(buggy_mutants, set_keys)
fixed_set = create_set_mutants(fixed_mutants, set_keys)
diff_set = buggy_set - fixed_set

diff_mutants = get_mutants_from_set(buggy_mutants, diff_set, set_keys, sort_on=0)

print(f"Caught {len(diff_set)} mutants in the diff set")

with open(root_dir / "diffset.log", "w") as f:
    f.writelines("...".join(mutant) + "\n" for mutant in diff_mutants)
