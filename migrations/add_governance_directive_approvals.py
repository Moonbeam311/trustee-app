import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.services_governance import ensure_governance_tables


if __name__ == "__main__":
    ensure_governance_tables()
    print("SUCCESS: IOS-3A directive approval columns created or verified.")
