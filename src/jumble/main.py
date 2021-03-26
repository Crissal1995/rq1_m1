from src.jumble import model
from src.utility import get_root_dir, get_class_name
import logging

FORMAT_VERBOSE = "%(levelname)s::%(module)s::%(lineno)d::%(asctime)s::%(message)s"
FORMAT = "%(levelname)s...%(asctime)s...%(message)s"

logging.basicConfig(filename="jumble.log", format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.info("---NEW EXECUTION---")

subject = "cli"
tool = "jumble"
root_dir = get_root_dir(subject=subject, tool=tool)
classname = get_class_name(subject=subject)

buggy_fp = root_dir / "buggy_out.txt"
fixed_fp = root_dir / "fixed_out.txt"

buggy_report = model.Report(buggy_fp)
fixed_report = model.Report(fixed_fp)

# stream content also on buggy
fh = logging.FileHandler("buggy.txt", mode="w")
logger.addHandler(fh)

logger.info("BUGGY VERSION")
logger.info(f"set length: {len(buggy_report.live_mutants)}")
logger.info(buggy_report)

logger.removeHandler(fh)

# stream content also on fixed.log
fh = logging.FileHandler("fixed.txt", mode="w")
logger.addHandler(fh)

logger.info("FIXED VERSION")
logger.info(f"set length: {len(fixed_report.live_mutants)}")
logger.info(fixed_report)

logger.removeHandler(fh)


fh = logging.FileHandler("diff.txt", mode="w")
logger.addHandler(fh)

logger.info("DIFF MUTANT SET")
comparer = model.ReportsComparer(buggy_report=buggy_report, fixed_report=fixed_report)
diff_mutants = comparer.compare_mutants(offset_line=938, offset_space=4)

logger.info(f"set length: {len(diff_mutants)}")
logger.info("\n".join([str(m) for m in diff_mutants]))

logger.removeHandler(fh)
