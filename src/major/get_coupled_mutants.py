import logging


def get_mutants(fp):
    with open(fp) as f:
        temp = [line.strip().split("...") for line in f.readlines()]
    return temp


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
