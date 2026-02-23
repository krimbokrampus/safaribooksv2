import gc
import json
from pathlib import Path
from typing import Tuple

import src.handler
from src.epub import TEST_ID, TEST_ID_2

id = input("Input ID: ")
handler.start(int(id))
