import re
from collections import defaultdict

from src import model


class Mutant(model.Mutant):
    counter = defaultdict(int)

    @classmethod
    def reset_counter(cls):
        cls.counter = defaultdict(int)

    @property
    def hash_tuple(self) -> tuple:
        return self.line, self.mutation, self.count

    def __init__(self, match):
        # tuple-like obj in the format
        # classname, line, mutation
        line = int(match[1])
        super().__init__(line=line)

        self.mutation: str = match[2].strip()

        # fix different mutations but with same line
        # and description with a counter
        key = (self.line, self.mutation)
        self.count = Mutant.counter[key]
        Mutant.counter[key] += 1

    def __str__(self):
        if self.line != self.original_line:
            org = f" (original: {self.original_line})"
        else:
            org = ""
        return f"Mutant at line {self.line}{org} with mutation: {self.mutation}"


class Report(model.Report):
    def get_killed_mutants(self):
        return []

    def get_live_mutants(self):
        return self.live_mutants

    def __init__(self, fp):
        self.filepath = fp
        self.live_mutants = None
        self.live_mutants_count = None
        self.killed_mutants_count = None

    def get_killed_mutants_count(self):
        return self.killed_mutants_count

    def get_mutants_count(self):
        return self.killed_mutants_count + self.live_mutants_count

    def makeit(self):
        # first reset counter
        Mutant.reset_counter()

        # then scrape the output
        fail_pattern = re.compile(r"M FAIL:\s*([a-zA-Z.]+):(\d+):\s*(.+)")
        start_pattern = re.compile(
            r"Mutation points = \d+, unit test time limit \d+\.\d+s"
        )
        end_pattern = re.compile(r"Jumbling took \d+\.\d+s")

        with open(self.filepath) as f:
            text = f.read()

        # get indices where the mutants are defined
        i = start_pattern.search(text).end()
        j = end_pattern.search(text[i:]).start() + i

        # subtract from text all the fails + get count of them
        killed_text, live_mutants_count = fail_pattern.subn("", text[i:j])

        # get killed count as length of mutations with whitespaces removed
        self.killed_mutants_count = len(re.sub(r"\s+", "", killed_text))

        # create live mutants as constructor over a match for all matches found
        self.live_mutants = [Mutant(match) for match in fail_pattern.findall(text[i:j])]
        self.live_mutants_count = len(self.live_mutants)

    def __repr__(self):
        str_mutants = "\n".join(str(mutant) for mutant in self.live_mutants)
        if not str_mutants:
            s = "No live mutants found!"
        else:
            s = str_mutants
        return s
