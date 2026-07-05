import sys
from pathlib import Path

# Add the workspace root to sys.path so we can import dataset_factory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset_factory.cli import main

if __name__ == "__main__":
    main()
