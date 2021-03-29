import xml.etree.ElementTree as ET

from src import model


class Mutant(model.Mutant):
    def __init__(self, element: ET.Element):
        DETECTED_STATUS = {"true": True, "false": False}

        attribs = element.attrib
        """detected is wether the mutant is detected
        (killed, timed out, memory error) or not (survived, not covered)."""
        self.detected = DETECTED_STATUS[attribs["detected"]]
        self.status = attribs["status"]

        children = list(element)
        assert len(children) == 10

        # rapid unpacking
        (
            self.source_file,  # java source file
            self.mutated_class,  # java class
            self.mutated_method,  # method name
            self.method_description,  # method args list
            line,  # str line number
            self.mutator,  # mutation operator
            self.index,  # ?
            self.block,  # ?
            self.killing_test,  # the test that killed this mutant, if any
            self.description,  # the description of what was done
        ) = [child.text for child in children]
        super().__init__(int(line))

    @property
    def hash_tuple(self) -> tuple:
        return (
            self.source_file,
            self.mutated_class,
            self.mutated_method,
            self.method_description,
            self.line,
            self.mutator,
            self.description,
        )

    def __repr__(self):
        if self.original_line != self.line:
            s = f" (original: {self.original_line})"
        else:
            s = ""
        return (
            f"Mutant at line {self.line}{s}"
            f" ({self.mutated_class} / {self.mutated_method} / {self.method_description})\n"
            f"Mutator {self.mutator} - {self.description}"
        )


class Report(model.Report):
    def __init__(self, filepath):
        self.filepath = filepath

        self.mutants = None
        self.killed_mutants = None
        self.live_mutants = None

    def makeit(self):
        tree = ET.parse(self.filepath)
        root = tree.getroot()
        children = list(root)
        mutants = []

        for child in children:
            mutants.append(Mutant(child))

        self.mutants = mutants
        self.killed_mutants = [mutation for mutation in mutants if mutation.detected]
        self.live_mutants = [mutation for mutation in mutants if not mutation.detected]
        assert len(self.killed_mutants) + len(self.live_mutants) == len(self.mutants)

        return self

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
