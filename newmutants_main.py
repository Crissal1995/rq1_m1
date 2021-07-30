import pathlib

from src.mutants import reports

projects = ["cli", "gson", "lang"]
classes = [
    "org.apache.commons.cli.HelpFormatter",
    "com.google.gson.stream.JsonWriter",
    "org.apache.commons.lang.time.DateUtils",
]


for project, cls in zip(projects, classes):
    p = pathlib.Path(f"data_cmp/{project}/judy/_single_dev/result.json")
    report = reports.JudyReport.from_file(p, class_under_mutation=cls)
    print(report)

    p = pathlib.Path(f"data_cmp/{project}/jumble/_single_dev/jumble_output.txt")
    report = reports.JumbleReport.from_file(p)
    print(report)

    p1 = pathlib.Path(f"data_cmp/{project}/major/_single_dev/kill.csv")
    p2 = pathlib.Path(f"data_cmp/{project}/major/_single_dev/mutants.log")
    report = reports.MajorReport.from_files([p1, p2])
    print(report)

    p = pathlib.Path(f"data_cmp/{project}/pit/_single_dev/mutations.xml")
    report = reports.PitReport.from_file(p)
    print(report)
