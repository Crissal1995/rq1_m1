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

    def __init__(self, match: re.Match):
        line = int(match.group(2))
        super().__init__(line=line)

        self.mutation: str = match.group(3).strip()

        # fix different mutations but with same line
        # and description with a counter
        key = (self.line, self.mutation)
        self.count = Mutant.counter[key]
        Mutant.counter[key] += 1

    def __repr__(self):
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

    def makeit(self):
        # first reset counter
        Mutant.reset_counter()

        # then scrape the output
        fail_pattern = re.compile(r"M FAIL:\s*([a-zA-Z.]+):(\d+):\s*(.+)")
        start_pattern = re.compile(
            r"Mutation points = \d+, unit test time limit \d+\.\d+s"
        )
        end_pattern = re.compile(r"Jumbling took \d+\.\d+s")

        lines = [line.strip() for line in open(self.filepath).readlines()]
        start_line_idx = (
            lines.index([line for line in lines if re.match(start_pattern, line)].pop())
            + 1
        )
        end_line_idx = lines.index(
            [line for line in lines if re.match(end_pattern, line)].pop()
        )

        live_mutants = []
        for line in lines[start_line_idx:end_line_idx]:
            match = re.search(fail_pattern, line)
            if match:
                live_mutants.append(Mutant(match=match))

        self.live_mutants = sorted(live_mutants, key=lambda m: m.line)

    def __repr__(self):
        str_mutants = "\n".join(str(mutant) for mutant in self.live_mutants)
        if not str_mutants:
            s = "No live mutants found!"
        else:
            s = str_mutants
        return s
