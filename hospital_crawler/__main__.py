"""python -m hospital_crawler 等同于 main.py。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import main

if __name__ == "__main__":
    main()
