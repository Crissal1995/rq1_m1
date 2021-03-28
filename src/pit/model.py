import xml.etree.ElementTree as ET

KILLED = 10
SURVIVED = 20
TIMED_OUT = 30
NO_COVERAGE = 40

# we use dicts to ensure there is no error on xml
# KeyError is raised if a key (xml value) is missing
MUTATION_STATUS = {
    "KILLED": KILLED,
    "SURVIVED": SURVIVED,
    "TIMED_OUT": TIMED_OUT,
    "NO_COVERAGE": NO_COVERAGE
}

DETECTED_STATUS = {
    "true": True,
    "false": False
}


class Mutation:
    def __init__(self, element: ET.Element):
        attribs = element.attrib
        """detected is wether the mutant is detected (killed or timed out) or not (survived or not covered)."""
        self.detected = DETECTED_STATUS[attribs["detected"]]
        self.status = MUTATION_STATUS[attribs["status"]]

        children = list(element)
        assert len(children) == 10

        # rapid unpacking
        self.source_file, \
            self.mutated_class, \
            self.mutated_method, \
            self.method_description, \
            self.line, \
            self.mutator, \
            self.index, \
            self.block, \
            self.killing_test, \
            self.description = [child.text for child in children]

        self.line = int(self.line)

        #
        # CHANGE THIS ATTR
        # to decide which attributes are used to determine if two mutations are different!
        # self.mutator removed because we have a pletora of different mutators that can lead to same result
        self._tuple = (
            self.mutated_class,
            self.mutated_method,
            self.method_description,
            self.line,
            self.description
        )

    def __repr__(self):
        return f"Mutant at line {self.line}" \
               f" ({self.mutated_class} / {self.mutated_method} / {self.method_description})\n" \
               f"Mutator {self.mutator} - {self.description}"

    def __hash__(self):
        return hash(self._tuple)

    def __eq__(self, other):
        if not isinstance(other, Mutation):
            return False
        return all(el1 == el2 for (el1, el2) in zip(self._tuple, other._tuple))


class Report:
    def __init__(self, filepath):
        tree = ET.parse(filepath)
        root = tree.getroot()
        children = list(root)
        mutations = []

        for child in children:
            child: ET.Element
            mutations.append(Mutation(child))

        self.mutations = mutations
        self.killed_mutations = [mutation for mutation in mutations if mutation.detected]
        self.live_mutations = [mutation for mutation in mutations if not mutation.detected]
        assert len(self.killed_mutations) + len(self.live_mutations) == len(self.mutations)

    def __repr__(self):
        str_live = "\n\n".join([str(mutation) for mutation in self.live_mutations])

        return f"Report\n" \
               f"Mutants total ({len(self.mutations)}), " \
               f"killed ({len(self.killed_mutations)}) / " \
               f"live ({len(self.live_mutations)})\n" \
               f"Live mutants:\n" \
               f"{str_live}"


class ReportsComparer:
    def __init__(self, buggy_report: Report, fixed_report: Report):
        self.buggy_report = buggy_report
        self.fixed_report = fixed_report

    def compare_mutants(self, offset_line: int, offset_space: int):
        buggy_mutants = self.buggy_report.live_mutations
        fixed_mutants = self.fixed_report.live_mutations

        # for every mutant, if it's line is >= offset line,
        # then add the offset space specified
        for i, mutant in enumerate(fixed_mutants):
            if mutant.line >= offset_line:
                fixed_mutants[i].line += offset_space

        set_buggy = set(buggy_mutants)
        set_fixed = set(fixed_mutants)
        diff_set = set_buggy.difference(set_fixed)

        return sorted(diff_set, key=lambda m: m.line)


if __name__ == "__main__":
    report = Report("../../data/cli32/pit/buggy/mutations.xml")
    print(report)
