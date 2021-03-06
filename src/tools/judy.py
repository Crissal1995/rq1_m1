import json
import os
from collections import defaultdict

from src import model


class MutantOperator:
    operators = {}

    @classmethod
    def reset_operators(cls):
        cls.operators = {}

    def __init__(self, adict):
        self.name: str = adict["name"]
        self.description: str = adict["description"]

        if self.name in self.operators:
            msg = (
                f"Found duplicate operator name! "
                f"{self.name} found, but got already {self.operators[self.name]}"
            )
            raise ValueError(msg)
        else:
            self.operators[self.name] = self

    @classmethod
    def find_by_name(cls, name: str):
        return cls.operators[name]

    def __repr__(self):
        return f"MutantOperator(name={self.name}, description={self.description})"


class Mutant(model.Mutant):
    counter = defaultdict(int)

    @classmethod
    def reset_counter(cls):
        cls.counter = defaultdict(int)

    @property
    def hash_tuple(self) -> tuple:
        return self._hash_tuple + (self._count,)

    @property
    def _hash_tuple(self) -> tuple:
        return self.line, self.operator.name

    def __init__(self, adict):
        lines = adict["lines"]
        operators = adict["operators"]
        points = adict["points"]

        assert all(len(thelist) == 1 for thelist in (lines, operators, points))

        line, operator, points = lines[0], operators[0], points[0]

        super().__init__(line=int(line))
        self.points: int = points
        self.operator = MutantOperator.find_by_name(operator)

        # fix different mutations but with same line
        # and description with a counter
        thehash = hash(self._hash_tuple)
        self._count = Mutant.counter[thehash]
        Mutant.counter[thehash] += 1

    def __str__(self):
        if self.original_line != self.line:
            s = f" (original: {self.original_line})"
        else:
            s = ""
        s = f"Mutant at line {self.line}{s} with"
        s += f" {self.points} points and"
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
        # reset counter when we create the report
        Mutant.reset_counter()

        with open(self.result_fp) as f:
            result = json.load(f)
        # instantiate operators to use them in Mutants
        self.operators = [MutantOperator(adict) for adict in result["operators"]]

        classdict = [
            thedict
            for thedict in result["classes"]
            if self.classname == thedict["name"]
        ]

        if not classdict:
            raise ValueError(
                f"{self.classname} not found in classes; file: {self.result_fp}"
            )
        elif len(classdict) > 1:
            raise ValueError(f"{self.classname} found 2+ times; file: {self.result_fp}")
        else:
            classdict = classdict[0]

        self.name = classdict["name"]
        self.total_mutants_count = classdict["mutantsCount"]
        self.killed_mutants_count = classdict["mutantsKilledCount"]
        self.live_mutants_count = self.total_mutants_count - self.killed_mutants_count
        self.live_mutants = [Mutant(mdict) for mdict in classdict["notKilledMutant"]]

        # at the end of execution, reset mutant operator dictionary
        MutantOperator.reset_operators()

    def get_live_mutants(self):
        return self.live_mutants

    def get_killed_mutants(self):
        return []

    def get_killed_mutants_count(self):
        return self.killed_mutants_count

    def get_mutants_count(self):
        return self.total_mutants_count

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
