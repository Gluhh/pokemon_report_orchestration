"""Start the local Prefect server."""

import subprocess
import sys


def main() -> None:
    print("Starting Prefect server at http://127.0.0.1:4200")
    subprocess.run([sys.executable, "-m", "prefect", "server", "start"], check=True)


if __name__ == "__main__":
    main()
