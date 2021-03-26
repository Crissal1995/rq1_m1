import re
from collections import defaultdict


class MutationCounter:
    counter = defaultdict(int)

    @classmethod
    def reset_counter(cls):
        cls.counter = defaultdict(int)

    @classmethod
    def get_count(cls, line: int, mutation: str):
        cls.counter[(line, mutation)] += 1
        return cls.counter[(line, mutation)]


class Mutant:
    def __init__(self, match: re.Match):
        self.line: int = int(match.group(2))
        self.mutation: str = match.group(3).strip()
        self.count = MutationCounter.get_count(line=self.line, mutation=self.mutation)

    def __hash__(self):
        return hash((self.line, self.mutation, self.count))

    def __eq__(self, other):
        if not isinstance(other, Mutant):
            return False
        return self.line == other.line and self.mutation == other.mutation and self.count == other.count

    def __repr__(self):
        return f"Mutant at line {self.line} with mutation: {self.mutation}"


class Report:
    def __init__(self, fp):
        fail_pattern = re.compile(r"M FAIL:\s*([a-zA-Z.]+):(\d+):\s*(.+)")
        start_pattern = re.compile(r"Mutation points = \d+, unit test time limit \d+\.\d+s")
        end_pattern = re.compile(r"Jumbling took \d+\.\d+s")

        lines = [line.strip() for line in open(fp).readlines()]
        start_line_idx = lines.index([line for line in lines if re.match(start_pattern, line)].pop())
        end_line_idx = lines.index([line for line in lines if re.match(end_pattern, line)].pop())

        MutationCounter.reset_counter()
        mutants = []

        for line in lines[start_line_idx + 1:end_line_idx]:
            match = re.search(fail_pattern, line)
            if match:
                mutants.append(Mutant(match=match))

        self.live_mutants = sorted(mutants, key=lambda m: m.line)

    def __repr__(self):
        str_mutants = "\n".join(str(mutant) for mutant in self.live_mutants)
        if not str_mutants:
            s = "No live mutants found!"
        else:
            s = str_mutants
        return s


class ReportsComparer:
    def __init__(self, buggy_report: Report, fixed_report: Report):
        self.buggy_report = buggy_report
        self.fixed_report = fixed_report

    def compare_mutants(self, offset_line: int, offset_space: int):
        buggy_mutants = self.buggy_report.live_mutants
        fixed_mutants = self.fixed_report.live_mutants

        # for every mutant, if it's line is >= offset line,
        # then add the offset space specified
        for i, mutant in enumerate(fixed_mutants):
            if mutant.line >= offset_line:
                fixed_mutants[i].line += offset_space

        print(fixed_mutants[0].__hash__())

        set_buggy = set(buggy_mutants)
        set_fixed = set(fixed_mutants)
        diff_set = set_buggy.difference(set_fixed)

        return sorted(diff_set, key=lambda m: m.line)
