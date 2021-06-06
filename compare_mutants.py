import argparse
import logging

from src.model import MutantsComparerSets
from src.utility import get_report, subjects, tools

# FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"
FORMAT = "%(levelname)s :: [%(module)s.%(lineno)d] :: %(message)s"

file_handler = logging.FileHandler("compare_mutants.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(FORMAT))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(FORMAT))

logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


def main():
    parser = argparse.ArgumentParser()

    # set one subject (cannot compare two different subjects)
    parser.add_argument("subject", choices=subjects)

    # set tool (cannot compare between two or more tools)
    parser.add_argument("tool", choices=tools)

    # set first and second files arguments
    parser.add_argument("-f1", "--files1", nargs="+")
    parser.add_argument("-f2", "--files2", nargs="+")

    # set root for files
    parser.add_argument("--root", default="data")

    args = parser.parse_args()

    root: str = args.root
    subject: str = args.subject

    tool: str = args.tool
    files1: [str] = args.files1
    files2: [str] = args.files2

    max_files_length = 2

    if len(args.files1) > max_files_length:
        parser.error(f"files1 can hold up to {max_files_length} arguments")

    if len(args.files2) > max_files_length:
        parser.error(f"files2 can hold up to {max_files_length} arguments")

    report1 = get_report(subject, tool, *files1, root=root)
    report1.makeit()

    report2 = get_report(subject, tool, *files2, root=root)
    report2.makeit()

    comparer = MutantsComparerSets(
        report1.get_live_mutants(), report2.get_live_mutants()
    )
    dirname = f"{subject} {tool}"
    comparer.summary(dirname=dirname)


if __name__ == "__main__":
    main()
