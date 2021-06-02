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

    # set first and second tools
    parser.add_argument("tool1", choices=tools)
    parser.add_argument("tool2", choices=tools)

    # set first and second files arguments
    parser.add_argument("-f1", "--files1", nargs="+")
    parser.add_argument("-f2", "--files2", nargs="+")

    # set root for files
    parser.add_argument("--root", default="data")

    args = parser.parse_args()
    print(args)

    max_files_length = 2
    if any(
        len(args.__getattribute__(s)) > max_files_length for s in ("files1", "files2")
    ):
        parser.error(f"filesX can hold up to {max_files_length} files")

    root: str = args.root
    subject: str = args.subject

    tool1: str = args.tool1
    files1: [str] = args.files1

    tool2: str = args.tool2
    files2: [str] = args.files2

    report1 = get_report(subject, tool1, *files1, root=root)
    report1.makeit()
    report2 = get_report(subject, tool2, *files2, root=root)
    report2.makeit()

    comparer = MutantsComparerSets(
        report1.get_live_mutants(), report2.get_live_mutants()
    )
    comparer.summary()


if __name__ == "__main__":
    main()
