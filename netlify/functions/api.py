import sys
from pathlib import Path

from mangum import Mangum

# Ensure backend modules are importable when running as a Netlify function.
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from main import app  # noqa: E402


handler = Mangum(app, api_gateway_base_path="/api")
