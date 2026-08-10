import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contracts.deploy import deploy_contract


if __name__ == "__main__":
    print(deploy_contract())
