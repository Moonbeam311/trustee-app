import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.services_governance import ensure_governance_tables


if __name__ == "__main__":
    ensure_governance_tables()
    print("SUCCESS: IOS-3A governance tables created or verified.")
