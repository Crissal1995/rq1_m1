import json


class MutantOperator:
    operators = {}

    def __init__(self, adict):
        self.name = adict["name"]
        self.description = adict["description"]
        MutantOperator.operators[self.name] = self

    @classmethod
    def find_by_name(cls, name: str):
        return cls.operators[name]

    def __repr__(self):
        return f"{self.name} [{self.description}]"


class Mutant:
    def __init__(self, adict):
        lines = adict["lines"]
        operators = adict["operators"]

        assert len(lines) == 1
        assert len(operators) == 1

        line = lines[0]
        operator = operators[0]

        self.line: int = line
        self.operator: MutantOperator = MutantOperator.find_by_name(operator)

    def __repr__(self):
        return f"Mutant found at line {self.line} with operator {self.operator}"


class MutatedClass:
    def __init__(self, adict):
        self.name = adict["name"]
        self.total_mutants_count = adict["mutantsCount"]
        self.killed_mutants_count = adict["mutantsKilledCount"]
        self.live_mutants_count = self.total_mutants_count - self.killed_mutants_count
        self.live_mutants = [Mutant(mdict) for mdict in adict["notKilledMutant"]]

    def __repr__(self):
        s = f"CLASS {self.name}\n"
        s += f"Total mutants: {self.total_mutants_count} -> "
        s += f"Killed: {self.killed_mutants_count}, Live: {self.live_mutants_count}"
        if self.live_mutants_count > 0:
            s += "\nLIVE MUTANTS:\n"
            s += "\n".join(repr(mutant) for mutant in sorted(self.live_mutants, key=lambda x: x.line))
        return s


class JudyResult:
    def __init__(self, result_fp, classname: str):
        with open(result_fp) as f:
            self.result = json.load(f)
        self.classname = classname
        self.operators = [MutantOperator(adict) for adict in self.result["operators"]]

    def get_classes(self):
        return [MutatedClass(adict) for adict in self.result["classes"] if self.classname in adict["name"]]

    def get_class(self):
        results = [MutatedClass(adict) for adict in self.result["classes"] if self.classname == adict["name"]]
        assert len(results) > 0, "No class found!"
        assert len(results) == 1, "Two or more classes found with this name!"
        return results[0]

    def __repr__(self):
        s = f"JUDY RESULT for class {self.classname}\n"
        classes = self.get_classes()
        s += "\n\n".join(repr(cls) for cls in sorted(classes, key=lambda x: x.name))
        return s
