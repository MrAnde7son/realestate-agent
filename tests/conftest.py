import sys
from pathlib import Path

# Ensure project root is on sys.path for absolute imports like 'db.database'
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
