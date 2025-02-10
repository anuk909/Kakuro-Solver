from typing import TypeAlias
from pathlib import Path
from dataclasses import dataclass
import json

Cell = tuple[int, int]  # (row, col)


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
    def __init__(self, size, cells):
        self.size: tuple[int, int] = size
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

    def is_wall(self, row: int, col: int) -> bool:
        cell = self.board.get((row, col))
        return cell and cell.is_wall

    def get_clue(self, row: int, col: int) -> ClueCell | None:
        return self.board.get((row, col))