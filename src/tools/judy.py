import json
import os

from src import model


class MutantOperator:
    operators = {}

    def __init__(self, adict):
        self.name: str = adict["name"]
        self.description: str = adict["description"]
        MutantOperator.operators[self.name] = self

    @classmethod
    def find_by_name(cls, name: str):
        return cls.operators[name]

    def __repr__(self):
        return f"MutantOperator(name={self.name}, description={self.description})"


class Mutant(model.Mutant):
    @property
    def hash_tuple(self) -> tuple:
        return self.line, self.operator

    def __init__(self, adict):
        lines = adict["lines"]
        operators = adict["operators"]
        points = adict["points"]

        assert all(len(thelist) == 1 for thelist in (lines, operators, points))

        line, operator, points = lines[0], operators[0], points[0]

        self.line: int = line
        self.points: int = points
        self.operator: MutantOperator = MutantOperator.find_by_name(operator)

    def __repr__(self):
        s = f"Mutant at line {self.line:4} with"
        s += f" {self.points:2} points and"
        s += f" operator {self.operator}"
        return s


class Report(model.Report):
    def __init__(self, result_fp: [str, os.PathLike], classname: str):
        self.result_fp = result_fp
        self.classname = classname

        self.operators = None
        self.name = None
        self.total_mutants_count = None
        self.killed_mutants_count = None
        self.live_mutants_count = None
        self.live_mutants = None

    def makeit(self):
        with open(self.result_fp) as f:
            result = json.load(f)
        # instantiate operators to use them in Mutants
        self.operators = [MutantOperator(adict) for adict in result["operators"]]

        classdict = [
            thedict
            for thedict in result["classes"]
            if self.classname == thedict["name"]
        ][0]
        self.name = classdict["name"]
        self.total_mutants_count = classdict["mutantsCount"]
        self.killed_mutants_count = classdict["mutantsKilledCount"]
        self.live_mutants_count = self.total_mutants_count - self.killed_mutants_count
        self.live_mutants = [Mutant(mdict) for mdict in classdict["notKilledMutant"]]
        return self

    def get_mutants(self):
        return self.get_live_mutants()

    def get_live_mutants(self):
        return self.live_mutants

    def get_killed_mutants(self):
        return []

    def __repr__(self):
        s = f"CLASS {self.name}\n"
        s += f"Total mutants: {self.total_mutants_count} -> "
        s += f"Killed: {self.killed_mutants_count}, Live: {self.live_mutants_count}"
        if self.live_mutants_count > 0:
            s += "\nLIVE MUTANTS:\n"
            s += "\n".join(
                repr(mutant)
                for mutant in sorted(self.live_mutants, key=lambda x: x.line)
            )
        return s
