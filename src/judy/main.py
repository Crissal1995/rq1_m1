from src.judy import model
from src.utility import get_root_dir, get_class_name
import logging

FORMAT_VERBOSE = "%(levelname)s::%(module)s::%(lineno)d::%(asctime)s::%(message)s"
FORMAT = "%(levelname)s...%(asctime)s...%(message)s"

logging.basicConfig(filename="judy.log", format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.info("---NEW EXECUTION---")

subject = "cli"
tool = "judy"
root_dir = get_root_dir(subject=subject, tool=tool)
classname = get_class_name(subject=subject)

buggy_fp = root_dir / "buggy_result.json"
fixed_fp = root_dir / "fixed_result.json"

buggy_result = model.JudyResult(buggy_fp, classname)
buggy_class = buggy_result.get_class()

fixed_result = model.JudyResult(fixed_fp, classname)
fixed_class = fixed_result.get_class()

# stream content also on buggy.log
fh = logging.FileHandler("buggy.txt", mode="w")
logger.addHandler(fh)

logger.info("BUGGY VERSION")
logger.info(buggy_result)

logger.removeHandler(fh)

# stream content also on fixed.log
fh = logging.FileHandler("fixed.txt", mode="w")
logger.addHandler(fh)

logger.info("FIXED VERSION")
logger.info(fixed_result)

logger.removeHandler(fh)
