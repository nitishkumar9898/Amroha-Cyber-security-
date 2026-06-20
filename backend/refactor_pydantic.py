import os
import glob

SCHEMA_DIR = "app/schemas"

def refactor_pydantic():
    files = glob.glob(os.path.join(SCHEMA_DIR, "*.py"))
    
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Ensure ConfigDict is imported if not already there
        if "ConfigDict" not in content and "from pydantic import" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("from pydantic import"):
                    if "ConfigDict" not in line:
                        lines[i] = line + ", ConfigDict"
                    break
            content = '\n'.join(lines)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Fixed imports in {file_path}")

if __name__ == "__main__":
    refactor_pydantic()
