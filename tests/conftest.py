import sys
from pathlib import Path

# Add repo root to sys.path so `from scripts.vision_parser import ...` works
sys.path.insert(0, str(Path(__file__).parent.parent))
