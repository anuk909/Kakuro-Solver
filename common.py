from typing import TypeAlias
from pathlib import Path
from dataclasses import dataclass
import json
from jsonschema import validate


Cell = tuple[int, int]  # (row, col)
PuzzleSize = tuple[int, int]

PUZZLE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "size": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
        },
        "cells": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "wall": {"type": "boolean"},
                    "right": {"type": "integer"},
                    "down": {"type": "integer"},
                },
                "required": ["x", "y"],
                "anyOf": [
                    {"required": ["wall"]},
                    {"required": ["right"]},
                    {"required": ["down"]},
                ],
            },
        },
        "solution_cells": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "value": {"type": "integer"},
                },
                "required": ["x", "y", "value"],
            },
        },
    },
    "required": ["size", "cells"],
}


def load_puzzle_data(file_path: str | Path) -> dict:
    """Load and validate puzzle data from JSON file."""
    with open(file_path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
    validate(instance=data, schema=PUZZLE_JSON_SCHEMA)
    return data


def pretty_json_str(puzzle: dict) -> str:
    """Returns json_str for puzzle dict that looks good"""
    validate(instance=puzzle, schema=PUZZLE_JSON_SCHEMA)
    has_solution = "solution_cells" in puzzle

    puzzle["cells"].sort(key=lambda cell: (cell["x"], cell["y"]))
    if has_solution:
        puzzle["solution_cells"].sort(key=lambda cell: (cell["x"], cell["y"]))

    size_str = f'[{puzzle["size"][0]}, {puzzle["size"][1]}]'

    # Format each cell object on one line with proper spacing
    cells_str = []
    for cell in puzzle["cells"]:
        parts = []
        for key, value in cell.items():
            if isinstance(value, bool):
                parts.append(f'"{key}": {str(value).lower()}')
            else:
                parts.append(f'"{key}": {value}')
        cell_str = "{ " + ", ".join(parts) + " }"
        cells_str.append("    " + cell_str)

    if has_solution:
        solution_cells_str = []
        for cell in puzzle["solution_cells"]:
            parts = []
            for key, value in cell.items():
                parts.append(f'"{key}": {value}')
            solution_cell_str = "{ " + ", ".join(parts) + " }"
            solution_cells_str.append("    " + solution_cell_str)

    # Build final JSON string with exact formatting
    json_str = "{\n"
    json_str += f'  "size": {size_str},\n'
    json_str += '  "cells": [\n'
    json_str += ",\n".join(cells_str)
    json_str += "\n  ],\n"
    if has_solution:
        json_str += '  "solution_cells": [\n'
        json_str += ",\n".join(solution_cells_str)
        json_str += "\n  ]\n"
    json_str += "}"

    # Make sure that final json is valid
    validate(json.loads(json_str), PUZZLE_JSON_SCHEMA)
    return json_str


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
        self.size = size
        self.board: dict[Cell, ClueCell] = {}
        for cell in cells:
            x, y = cell["x"], cell["y"]
            row_sum = cell.get("right")
            col_sum = cell.get("down")
            # Support writing wall explicit or implicit
            is_wall = cell.get("wall") or row_sum or col_sum
            if is_wall:
                self.board[(x, y)] = ClueCell(x, y, row_sum, col_sum, is_wall)

    @property
    def clues(self):
        return self.board.values()

    def is_wall(self, col: int, row: int) -> bool:
        cell = self.board.get((col, row))
        return cell and cell.is_wall

    def get_clue(self, col: int, row: int) -> ClueCell | None:
        return self.board.get((col, row))
