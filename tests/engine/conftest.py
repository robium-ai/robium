import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hooks" / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "engine"))
sys.path.insert(0, str(REPO / "skills" / "skill-author" / "scripts"))
