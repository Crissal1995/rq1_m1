import json


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
        return f"{self.name} [{self.description}]"

    def __eq__(self, other):
        if not isinstance(other, MutantOperator):
            return False
        return self.name.lower() == other.name.lower()


class Mutant:
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
        return f"Mutant at line {self.line:4}, with {self.points:2} points and operator {self.operator}"

    def __eq__(self, other):
        if not isinstance(other, Mutant):
            return False
        return self.line == other.line and self.operator == other.operator and self.points == self.points

    def __hash__(self):
        # should points be inside hash function?
        return hash((self.line, self.operator.name))


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


class Result:
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
        s = f"RESULT for class {self.classname}\n"
        classes = self.get_classes()
        s += "\n\n".join(repr(cls) for cls in sorted(classes, key=lambda x: x.name))
        return s


class ResultsComparer:
    def __init__(self, buggy_result: Result, fixed_result: Result, changed_lines_buggy=None, changed_lines_fixed=None):
        """Buggy and fixed results are Result object

        changed_lines_* are lists that include lines added/deleted (as seen in git diffs);
        for example, given a list X of elements xi, if xi is positive, that line is added in
        the output of a git diff; if xi is negative, then -xi is positive and is the line deleted.
        """
        self.buggy = buggy_result
        self.fixed = fixed_result

        # TODO understand how to match lines between buggy and fixed version
        self.changed_lines_buggy = changed_lines_buggy or []
        self.changed_lines_fixed = changed_lines_fixed or []

        added_buggy = sum(1 for el in self.changed_lines_buggy if el > 0)
        deleted_buggy = sum(1 for el in self.changed_lines_buggy if el < 0)

        added_fixed = sum(1 for el in self.changed_lines_fixed if el > 0)
        deleted_fixed = sum(1 for el in self.changed_lines_fixed if el < 0)

        self.added_buggy = added_buggy - deleted_buggy
        self.added_fixed = added_fixed - deleted_fixed

        """total added is how many lines are added (if positive) 
        or removed (if negative) from buggy to fixed source code
        
        Example: HelpFormatter, from buggy to fixed, loses lines
        from 937 to 941 but gains line 937, so in total 1 - 5 = 4 lines were removed
        
        In our case
        added_buggy = 0 - 5 = -5
        added_fixed = 1 - 0 = 1
        total_added = 1 + (-5) = -4
        """
        self.total_added = self.added_fixed + self.added_buggy

    def compare_mutants(self, offset_line=None, offset_space=None):
        buggy_mutants = self.buggy.get_class().live_mutants
        fixed_mutants = self.fixed.get_class().live_mutants

        # for every mutant, if it's line is >= offset line,
        # then add the offset space specified
        if offset_line and offset_space:
            for i, mutant in enumerate(fixed_mutants):
                if mutant.line >= offset_line:
                    fixed_mutants[i].line += offset_space

        set_buggy = set(buggy_mutants)
        set_fixed = set(fixed_mutants)
        diff_set = set_buggy - set_fixed

        return sorted(diff_set, key=lambda m: m.line)
