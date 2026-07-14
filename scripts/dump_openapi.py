"""Write the OpenAPI schema to openapi.json, for the frontend's client codegen.

Runs without a database: building the app performs no I/O.

    uv run python scripts/dump_openapi.py
"""

import json
from pathlib import Path

from bloom.main import app

OUTPUT = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
