import os
import glob
import re

def fix_models():
    models_dir = r"backend\app\models"
    for filepath in glob.glob(os.path.join(models_dir, "*.py")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace metadata = Column(...) with additional_metadata = Column("metadata", ...)
        new_content = re.sub(
            r'(\s+)metadata\s*=\s*Column\(([^,]+)(.*?)\)',
            r'\1additional_metadata = Column("metadata", \2\3)',
            content
        )
        
        # If any changes were made, write back
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed model: {filepath}")

def fix_schemas():
    schemas_dir = r"backend\app\schemas"
    for filepath in glob.glob(os.path.join(schemas_dir, "*.py")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace metadata: Optional[Dict[...]]
        new_content = re.sub(
            r'(\s+)metadata(\s*:\s*Optional\[Dict)',
            r'\1additional_metadata\2',
            content
        )
        new_content = re.sub(
            r'(\s+)metadata(\s*:\s*Dict)',
            r'\1additional_metadata\2',
            new_content
        )
        
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed schema: {filepath}")

def fix_services():
    services_dir = r"backend\app\services"
    for filepath in glob.glob(os.path.join(services_dir, "*.py")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace occurrences of .metadata and metadata=
        new_content = re.sub(r'\.metadata\b', r'.additional_metadata', content)
        new_content = re.sub(r'\bmetadata=payload\.', r'additional_metadata=payload.', new_content)
        new_content = re.sub(r'\bmetadata=record\.', r'additional_metadata=record.', new_content)
        new_content = re.sub(r'"metadata":\s*rec\.additional_metadata', r'"additional_metadata": rec.additional_metadata', new_content)
        new_content = re.sub(r'"metadata":\s*rec\.metadata', r'"additional_metadata": rec.additional_metadata', new_content)
        
        # In service files, if it's instantiating an object, it might be doing metadata=payload.metadata, which becomes additional_metadata=payload.additional_metadata
        # Let's also do a pass to replace `metadata=` with `additional_metadata=` if it's inside model instantiation
        new_content = re.sub(r'(\s+)metadata=(payload|data)\.additional_metadata', r'\1additional_metadata=\2.additional_metadata', new_content)
        
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed service: {filepath}")

if __name__ == "__main__":
    fix_models()
    fix_schemas()
    fix_services()
