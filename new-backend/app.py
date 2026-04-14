# AI assisted development
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_talent = _root / "talent-intelligence-service"
if str(_talent) not in sys.path:
    sys.path.insert(0, str(_talent))

from talent_intelligence.main import app
