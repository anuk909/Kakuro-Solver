from typing import TypeAlias, Optional, Union, Literal
from pathlib import Path
from dataclasses import dataclass
import json

Cell = tuple[int, int]  # (row, col)
PuzzleSize = tuple[int, int]
CellCoord = tuple[int, int]
ValidationResult = tuple[bool, Optional[str]]
DifficultyLevel = Literal["easy", "intermediate", "hard", "challenging", "expert"]


@dataclass
class SolutionCell:
    x: int
    y: int
    value: int


Solution: TypeAlias = list[SolutionCell]


@dataclass
class ClueCell:
    x: int
    y: int
    row_sum: int | None
    col_sum: int | None
    is_wall: bool


class KakuroPuzzle:
    def __init__(self, size: PuzzleSize, cells: list[dict]):
        """Initialize puzzle with validated data."""
        is_valid, error = validate_puzzle_data({"size": list(size), "cells": cells})
        if not is_valid:
            raise ValueError(f"Invalid puzzle data: {error}")
            
        self.size = size
        self.board: dict[CellCoord, ClueCell] = {}
        for cell in cells:
            x, y = cell["x"], cell["y"]
            row_sum = cell.get("right")
            col_sum = cell.get("down")
            # Support writing wall explicit or implicit
            has_wall = cell.get("wall", False)
            has_clue = row_sum is not None or col_sum is not None
            if has_wall or has_clue:
                self.board[(x, y)] = ClueCell(x, y, row_sum, col_sum, True)

    @property
    def clues(self):
        return self.board.values()

    def is_wall(self, row: int, col: int) -> bool:
        cell = self.board.get((row, col))
        return bool(cell and cell.is_wall)

    def get_clue(self, row: int, col: int) -> ClueCell | None:
        return self.board.get((row, col))

def validate_puzzle_data(data: dict) -> ValidationResult:
    """Validate raw puzzle JSON data."""
    if not isinstance(data.get("size"), list):
        return False, "size must be a list"
    
    if len(data["size"]) != 2:
        return False, "size must contain exactly 2 elements [rows, cols]"
    
    if not all(isinstance(x, int) for x in data["size"]):
        return False, "size elements must be integers"
    
    if not isinstance(data.get("cells"), list):
        return False, "cells must be a list"
    
    for i, cell in enumerate(data["cells"]):
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

def load_puzzle_data(file_path: str | Path) -> dict:
    """Load and validate puzzle data from JSON file."""
    with open(file_path) as f:
        data = json.load(f)
    is_valid, error = validate_puzzle_data(data)
    if not is_valid:
        raise ValueError(f"Invalid puzzle data: {error}")
    return data
