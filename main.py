import logging

from src import MutantError, ReportFactory, subjects, tools

# FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"
FORMAT = "%(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"

file_handler = logging.FileHandler("main.log", mode="w")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(FORMAT))

file_debug_handler = logging.FileHandler("main.debug.log", mode="w")
file_debug_handler.setLevel(logging.DEBUG)
file_debug_handler.setFormatter(logging.Formatter(FORMAT))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(FORMAT))

logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(file_debug_handler)
logger.setLevel(logging.DEBUG)


def main(base_dir="data"):
    for subject in subjects:
        for tool in tools:
            logging.warning(f"Working on subject {subject} and tool {tool}")
            try:
                factory = ReportFactory(tool=tool, subject=subject, base_dir=base_dir)
                factory.write_all_mutants()
            except MutantError as e:
                logging.error(f"Mutant error caught: {e}")
            except Exception as e:
                logging.error(f"Exception caught: {e}")


if __name__ == "__main__":
    main(base_dir="data_dummy")
