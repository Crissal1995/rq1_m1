import pathlib

# file.py -> src dir -> root dir
HOME = pathlib.Path(__file__).parent.parent

subjects = {"cli": "cli32", "lang": "lang53", "gson": "gson15"}
classnames = {
    "cli": "org.apache.commons.cli.HelpFormatter",
    "gson": "com.google.gson.stream.JsonWriter",
    "lang": "org.apache.commons.lang.time.DateUtils",
}
tools = ["judy", "jumble", "major", "pit"]


def get_root_dir(subject: str, tool: str):
    assert subject in subjects
    assert tool in tools
    return HOME / "data" / subjects[subject] / tool


def get_class_name(subject: str):
    assert subject in classnames
    return classnames[subject]
