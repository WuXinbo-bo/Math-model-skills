import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

import pandas as pd
df = pd.read_excel(resolve_workspace() / "data" / "soil_moisture.xlsx")
print("Columns:", list(df.columns[:5]))
print("First 5 rows:")
print(df.head())
print(f"Shape: {df.shape}")
