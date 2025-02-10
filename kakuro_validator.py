import json
import os
from typing import Dict, Optional, Tuple

def validate_puzzle_format(puzzle: Dict) -> Tuple[bool, Optional[str]]:
    """Validate puzzle matches required format."""
    if not isinstance(puzzle.get("size"), list):
        return False, "size must be a list"
    
    if len(puzzle["size"]) != 2:
        return False, "size must contain exactly 2 elements [rows, cols]"
    
    if not all(isinstance(x, int) for x in puzzle["size"]):
        return False, "size elements must be integers"
    
    if not isinstance(puzzle.get("cells"), list):
        return False, "cells must be a list"
    
    for i, cell in enumerate(puzzle["cells"]):
        if not isinstance(cell, dict):
            return False, f"cell {i} must be a dictionary"
            
        if "x" not in cell or "y" not in cell:
            return False, f"cell {i} missing x or y coordinates"
            
        if not isinstance(cell["x"], int) or not isinstance(cell["y"], int):
            return False, f"cell {i} coordinates must be integers"
        
        if "wall" in cell and not isinstance(cell["wall"], bool):
            return False, f"cell {i} wall must be boolean"
        
        if "right" in cell and not isinstance(cell["right"], int):
            return False, f"cell {i} right sum must be integer"
        
        if "down" in cell and not isinstance(cell["down"], int):
            return False, f"cell {i} down sum must be integer"
            
        if "value" in cell and not isinstance(cell["value"], int):
            return False, f"cell {i} value must be integer"
            
        if "value" in cell and not (1 <= cell["value"] <= 9):
            return False, f"cell {i} value must be between 1 and 9"
    
    return True, None

def main():
    puzzles_dir = "puzzles"
    if not os.path.exists(puzzles_dir):
        print("No puzzles directory found")
        return
        
    for filename in os.listdir(puzzles_dir):
        if filename.startswith("scraped_") and filename.endswith(".json"):
            filepath = os.path.join(puzzles_dir, filename)
            with open(filepath) as f:
                puzzle = json.load(f)
            
            is_valid, error = validate_puzzle_format(puzzle)
            if is_valid:
                print(f"✓ {filename} is valid")
            else:
                print(f"✗ {filename} is invalid: {error}")

if __name__ == "__main__":
    main()
