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
