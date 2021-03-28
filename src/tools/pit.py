import xml.etree.ElementTree as ET

from src import model

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
    "NO_COVERAGE": NO_COVERAGE,
}

DETECTED_STATUS = {"true": True, "false": False}


class Mutant(model.Mutant):
    def __init__(self, element: ET.Element):
        attribs = element.attrib
        """detected is wether the mutant is detected
        (killed or timed out) or not (survived or not covered)."""
        self.detected = DETECTED_STATUS[attribs["detected"]]
        self.status = MUTATION_STATUS[attribs["status"]]

        children = list(element)
        assert len(children) == 10

        # rapid unpacking
        (
            self.source_file,
            self.mutated_class,
            self.mutated_method,
            self.method_description,
            line,
            self.mutator,
            self.index,
            self.block,
            self.killing_test,
            self.description,
        ) = [child.text.strip() for child in children]
        super().__init__(int(line))

    @property
    def hash_tuple(self) -> tuple:
        return (
            self.source_file,
            self.mutated_class,
            self.mutated_method,
            self.method_description,
            self.line,
            self.description,
        )

    def __repr__(self):
        return (
            f"Mutant at line {self.line}"
            f" ({self.mutated_class} / {self.mutated_method} / {self.method_description})\n"
            f"Mutator {self.mutator} - {self.description}"
        )


class Report(model.Report):
    def __init__(self, filepath):
        tree = ET.parse(filepath)
        root = tree.getroot()
        children = list(root)
        mutants = []

        for child in children:
            mutants.append(Mutant(child))

        self.mutants = mutants
        self.killed_mutants = [mutation for mutation in mutants if mutation.detected]
        self.live_mutants = [mutation for mutation in mutants if not mutation.detected]
        assert len(self.killed_mutants) + len(self.live_mutants) == len(self.mutants)

    def get_mutants(self):
        return self.mutants

    def get_killed_mutants(self):
        return self.killed_mutants

    def get_live_mutants(self):
        return self.live_mutants

    def __repr__(self):
        str_live = "\n\n".join([str(mutation) for mutation in self.live_mutants])

        return (
            f"Report\n"
            f"Mutants total ({len(self.mutants)}), "
            f"killed ({len(self.killed_mutants)}) / "
            f"live ({len(self.live_mutants)})\n"
            f"Live mutants:\n"
            f"{str_live}"
        )
