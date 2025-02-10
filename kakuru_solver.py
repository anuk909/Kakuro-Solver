from z3 import *
import json
import argparse
from typing import TypeAlias, Optional
from dataclasses import dataclass
from pathlib import Path

# Type definitions
Cell = tuple[int, int]  # (row, col)
Solution: TypeAlias = list[list[int]]


@dataclass
class KakuroCell:
    x: int
    y: int
    row_sum: int | None
    col_sum: int | None
    is_wall: bool


class KakuroPuzzle:
    def __init__(self, size, cells):
        self.size: tuple[int, int] = size
        self.board: dict[Cell, KakuroCell] = {}
        for cell in cells:
            x, y = cell["x"], cell["y"]
            row_sum = cell.get("right")
            col_sum = cell.get("down")
            is_wall = cell.get("wall") or row_sum or col_sum
            if is_wall:
                self.board[(x, y)] = KakuroCell(x, y, row_sum, col_sum, is_wall)

    @property
    def clues(self):
        return self.board.values()

    def is_wall(self, row: int, col: int) -> bool:
        cell = self.board.get((row, col))
        return cell and cell.is_wall

    def get_clue(self, row: int, col: int) -> KakuroCell | None:
        return self.board.get((row, col))


def get_sum_run(
    puzzle: KakuroPuzzle, first_x: int, first_y: int, direction: str
) -> tuple[int, list[Cell]]:
    """Get cells involved in a sum run starting from a clue cell"""
    rows, cols = puzzle.size
    cells = []

    if direction == "right":
        for x in range(first_x + 1, cols):
            if puzzle.is_wall(x, first_y):
                break
            cells.append((x, first_y))
    else:
        for y in range(first_y + 1, rows):
            if puzzle.is_wall(first_x, y):
                break
            cells.append((first_x, y))

    return len(cells), cells


def solve_kakuro(puzzle: KakuroPuzzle) -> Solution | None:
    """Solve a Kakuro puzzle using Z3 SMT solver"""
    rows, cols = puzzle.size
    solver = Solver()

    # Create grid of Z3 variables
    grid = [[Int(f"cell_{i}_{j}") for j in range(cols)] for i in range(rows)]

    # Add basic constraints
    for i in range(rows):
        for j in range(cols):
            if puzzle.is_wall(i, j):
                solver.add(grid[i][j] == 0)
            else:
                solver.add(grid[i][j] >= 1)
                solver.add(grid[i][j] <= 9)

    # Add sum constraints
    for clue in puzzle.clues:
        x, y, row_sum, col_sum = clue.x, clue.y, clue.row_sum, clue.col_sum
        # Add right sum constraint
        if row_sum is not None:
            _, right_cells = get_sum_run(puzzle, x, y, "right")
            if right_cells:
                cell_vars = [grid[r][c] for r, c in right_cells]
                solver.add(Sum(cell_vars) == row_sum)
                solver.add(Distinct(cell_vars))

        # Add down sum constraint
        if col_sum is not None:
            _, down_cells = get_sum_run(puzzle, x, y, "down")
            if down_cells:
                cell_vars = [grid[r][c] for r, c in down_cells]
                solver.add(Sum(cell_vars) == col_sum)
                solver.add(Distinct(cell_vars))

    if solver.check() == sat:
        model = solver.model()
        return [
            [model.evaluate(grid[i][j]).as_long() for j in range(cols)]
            for i in range(rows)
        ]
    return None


def create_svg(
    puzzle: KakuroPuzzle,
    solution: Optional[Solution] = None,
    show_solution: bool = True,
) -> str:
    """Create SVG representation of the puzzle/solution"""
    cell_size = 60
    rows, cols = puzzle.size
    width = cols * cell_size
    height = rows * cell_size

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: white;">',
        "<style>",
        ".grid-line { stroke: #000; stroke-width: 1; }",
        ".wall { fill: #808080; stroke: #000; stroke-width: 1; }",
        ".clue { fill: #808080; stroke: #000; stroke-width: 1; }",
        ".blank { fill: #ffffff; stroke: #000; stroke-width: 1; }",
        ".clue-text { font-family: Arial,; font-size: 12px; fill: #000; }",
        ".solution { font-family: Arial; font-size: 24px; fill: #000; text-anchor: middle; dominant-baseline: middle; }",
        "</style>",
    ]

    # Draw cells
    for i in range(rows):
        for j in range(cols):
            x = i * cell_size
            y = j * cell_size

            if clue := puzzle.get_clue(i, j):
                row_sum, col_sum = clue.row_sum, clue.col_sum
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" class="clue"/>'
                )
                svg_lines.append(
                    f'<line x1="{x}" y1="{y}" x2="{x+cell_size}" y2="{y+cell_size}" class="grid-line"/>'
                )

                if row_sum is not None:
                    svg_lines.append(
                        f'<text x="{x+cell_size-20}" y="{y+20}" class="clue-text">{row_sum}</text>'
                    )
                if col_sum is not None:
                    svg_lines.append(
                        f'<text x="{x+10}" y="{y+cell_size-10}" class="clue-text">{col_sum}</text>'
                    )
            elif puzzle.is_wall(i, j):
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" class="wall"/>'
                )
            else:
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" class="blank"/>'
                )
                if show_solution and solution and solution[i][j] != 0:
                    svg_lines.append(
                        f'<text x="{x+cell_size/2}" y="{y+cell_size/2}" class="solution">{solution[i][j]}</text>'
                    )

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Kakuro Puzzle Solver")
    parser.add_argument(
        "--input", "-i", type=Path, required=True, help="Input puzzle file (JSON)"
    )
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output file")
    parser.add_argument(
        "--mode",
        choices=["show", "solve"],
        default="solve",
        help="Mode of operation",
    )
    args = parser.parse_args()

    with open(args.input, "r") as f:
        puzzle_data = json.load(f)
    puzzle = KakuroPuzzle(puzzle_data["size"], puzzle_data["cells"])

    if args.mode == "show":
        output = create_svg(puzzle, show_solution=False)
    elif args.mode == "solve":
        solution = solve_kakuro(puzzle)
        if solution is None:
            print("No solution exists")
            return
        output = create_svg(puzzle, solution)

    args.output.write_text(output)


if __name__ == "__main__":
    main()
