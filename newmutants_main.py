import pathlib

from src.mutants import reports

p = pathlib.Path("data_cmp/cli/judy/_single_dev/result.json")
report = reports.JudyReport.from_file(
    p, class_under_mutation="org.apache.commons.cli.HelpFormatter"
)
print(report)

p = pathlib.Path("data_cmp/cli/jumble/_single_dev/jumble_output.txt")
report = reports.JumbleReport.from_file(p)
print(report)

p1 = pathlib.Path("data_cmp/cli/major/_single_dev/kill.csv")
p2 = pathlib.Path("data_cmp/cli/major/_single_dev/mutants.log")
report = reports.MajorReport.from_files([p1, p2])
print(report)

p = pathlib.Path("data_cmp/cli/pit/_single_dev/mutations.xml")
report = reports.PitReport.from_file(p)
print(report)
