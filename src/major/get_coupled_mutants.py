import pathlib
import logging

# file.py -> major dir -> src dir -> root dir
HOME = pathlib.Path(__file__).parent.parent.parent

FORMAT = "%(levelname)s::%(message)s"

logging.basicConfig(filename="major.log", format=FORMAT, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("---NEW EXECUTION---")

directory = HOME / "data/cli32/major"
buggy = directory / "buggy"
fixed = directory / "fixed"
fname = "generated_live_mutants.log"


def get_mutants(fp):
    with open(fp) as f:
        temp = [line.strip().split("...") for line in f.readlines()]
    return temp


buggy_mutants = get_mutants(buggy / fname)
fixed_mutants = get_mutants(fixed / fname)


def create_set_mutants(mutants, keys=(1, 2), delimiter="_"):
    """Mutants is a list of mutants, and each mutant is in the format
    mutant_id, mutant_operator, mutant_line, mutation made

    Keys are the index of the mutant to take as hash key for the set,
    so two mutants are equal if mutantA[key] == mutantB[key], or
    the respective fields are equal.
    """
    assert isinstance(keys, (tuple, list))  # sequence
    s = set()
    for mutant in mutants:
        key = delimiter.join(mutant[k] for k in keys)
        s.add(key)
    return s


keys = (1, 2, 4)

buggy_set = create_set_mutants(buggy_mutants, keys=keys)
fixed_set = create_set_mutants(fixed_mutants, keys=keys)

# get elements that are found in buggy but NOT in fixed
diff_set = buggy_set - fixed_set

logging.info(f"Buggy set of mutants: {buggy_set}")
logging.info(f"Fixed set of mutants: {fixed_set}")
logging.info(f"Difference set of mutants: {diff_set}")


def get_mutants_from_set(mutants, mutant_set, keys=(1, 2), delimiter="_", sort_on=None):
    """Retrieve mutants from a set (that is a subset of mutants),
    based on the key of the set and the respective values for the mutant.
    """
    assert isinstance(keys, (tuple, list))  # sequence

    mutants_retrieved = []
    for mutant_key in mutant_set:
        logging.info(f"Working on {mutant_key}")
        elements = str(mutant_key).split(delimiter)

        assert len(elements) == len(keys), \
            f"Set key is made up of {len(elements)} elements, so your keys length must match!"
        # get mutant(s) if all elements match, that are
        # mutant[k] and elements[i] in order
        # ex.
        # mutant[1] == elements[0] and mutant[2] == elements[1] and so on
        mutants_found = [
            mutant
            for mutant in mutants
            if all(mutant[k] == elements[i] for k, i in zip(keys, range(len(keys))))
        ]
        if len(mutants_found) == 0:
            logging.error("No mutant found for this key")
            quit(1)
        elif len(mutants_found) > 1:
            logging.error("Two or more mutants found for this key")
            quit(1)
        else:
            mutant = mutants_found[0]
            mutants_retrieved.append(mutant)

    assert len(mutants_retrieved) == len(mutant_set), "Not every mutant was found!"
    if sort_on is not None:
        mutants_retrieved = sorted(mutants_retrieved, key=lambda x: x[sort_on])
    return mutants_retrieved


diff_mutants = get_mutants_from_set(mutants=buggy_mutants, mutant_set=diff_set, keys=keys, sort_on=2)

logging.info(f"Caught {len(diff_set)} mutants in the diff set")

with open(directory / "diffset.log", "w") as f:
    f.writelines("...".join(mutant) + "\n" for mutant in diff_mutants)
