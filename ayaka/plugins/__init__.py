import importlib
from pathlib import Path

path = Path(__file__).parent

for p in path.iterdir():
    if p.suffix == ".py" and not p.name.startswith("_"):
        module_name = f"ayaka.plugins.{p.stem}"
        importlib.import_module(module_name)
