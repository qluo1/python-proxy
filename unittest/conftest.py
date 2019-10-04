import pathlib
import sys
import logging

cur_dir = pathlib.Path(__file__).parent.resolve()
log_dir = cur_dir / ".." / "log"
proj_dir = str(cur_dir.parent)

if proj_dir not in sys.path:
    sys.path.insert(0, proj_dir)


logging.basicConfig(
    filename=log_dir / "unittest.log",
    level="DEBUG",
    format="%(asctime)s %(levelname)s %(message)s",
)
