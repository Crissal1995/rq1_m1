import logging

from src import utility

FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"

logging.basicConfig(filename="main.log", format=FORMAT, level=logging.DEBUG)

file_handler = logging.FileHandler("main.log")
file_handler.setFormatter(logging.Formatter(FORMAT))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(FORMAT))

logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(stream_handler)

for tool in utility.tools:
    for subject in utility.subjects:
        try:
            factory = utility.ReportFactory(tool=tool, subject=subject)
        except Exception as e:
            logging.error(f"TOOL: {tool}, SUBJECT: {subject}, ERROR: {e}")
        else:
            factory.write_mutants()
