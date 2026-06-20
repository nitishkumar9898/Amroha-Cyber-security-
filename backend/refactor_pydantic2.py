import os
import glob
import re

SCHEMA_DIR = "app/schemas"

def refactor_pydantic():
    files = glob.glob(os.path.join(SCHEMA_DIR, "*.py"))
    
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # If ConfigDict is used but not imported, import it
        if "ConfigDict" in content and "import ConfigDict" not in content and "ConfigDict," not in content and ", ConfigDict" not in content:
            # Add from pydantic import ConfigDict at the top
            content = "from pydantic import ConfigDict\n" + content
            
        # The previous run replaced `class Config:` in __init__.py but didn't import ConfigDict.
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Fixed {file_path}")

if __name__ == "__main__":
    refactor_pydantic()
