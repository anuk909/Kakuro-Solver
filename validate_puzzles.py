import json
import os
from typing import Dict

def validate_puzzle_format(puzzle: Dict) -> bool:
    """Validate puzzle matches required format."""
    if not isinstance(puzzle.get("size"), list) or len(puzzle["size"]) != 2:
        return False
    
    if not isinstance(puzzle.get("cells"), list):
        return False
    
    for cell in puzzle["cells"]:
        if not isinstance(cell, dict) or "x" not in cell or "y" not in cell:
            return False
        
        if "wall" in cell and not isinstance(cell["wall"], bool):
            return False
        
        if "right" in cell and not isinstance(cell["right"], int):
            return False
        
        if "down" in cell and not isinstance(cell["down"], int):
            return False
    
    return True

def main():
    examples_dir = "examples"
    for filename in os.listdir(examples_dir):
        if filename.startswith("scraped_") and filename.endswith(".json"):
            filepath = os.path.join(examples_dir, filename)
            with open(filepath) as f:
                puzzle = json.load(f)
            
            if validate_puzzle_format(puzzle):
                print(f"✓ {filename} is valid")
            else:
                print(f"✗ {filename} is invalid")

if __name__ == "__main__":
    main()
