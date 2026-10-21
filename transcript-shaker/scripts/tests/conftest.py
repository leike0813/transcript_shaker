"""让测试可以直接 import transcript_shaker（scripts/ 在 sys.path 上）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
