from z3 import *
import json
import argparse
from pathlib import Path
from common import KakuroPuzzle, Solution, Cell, SolutionCell, load_puzzle_data


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

    return cells


def solve_kakuro(puzzle: KakuroPuzzle) -> Solution | None:
    """Solve a Kakuro puzzle using Z3 SMT solver"""
    rows, cols = puzzle.size
    solver = Solver()

    # Create grid of Z3 variables
    grid = [[Int(f"cell_{col}_{row}") for row in range(rows)] for col in range(cols)]

    # Add basic constraints
    for row in range(rows):
        for col in range(cols):
            if clue := puzzle.get_clue(col, row):
                solver.add(grid[col][row] == 0)
            else:
                solver.add(grid[col][row] >= 1)
                solver.add(grid[col][row] <= 9)

    # Add sum constraints
    for clue in puzzle.clues:
        x, y, row_sum, col_sum = clue.x, clue.y, clue.row_sum, clue.col_sum
        # Add right sum constraint
        if row_sum is not None:
            if right_cells := get_sum_run(puzzle, x, y, "right"):
                cell_vars = [grid[col][row] for col, row in right_cells]
                solver.add(Sum(cell_vars) == row_sum)
                solver.add(Distinct(cell_vars))

        # Add down sum constraint
        if col_sum is not None:
            if down_cells := get_sum_run(puzzle, x, y, "down"):
                cell_vars = [grid[col][row] for col, row in down_cells]
                solver.add(Sum(cell_vars) == col_sum)
                solver.add(Distinct(cell_vars))

    if solver.check() == sat:
        model = solver.model()
        solution_cells = []

        for col in range(cols):
            for row in range(rows):
                if value := model.evaluate(grid[col][row]).as_long() and value > 0:
                    solution_cells.append(SolutionCell(col, row, value))

        return solution_cells
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Kakuro Puzzle Solver")
    parser.add_argument(
        "--input", "-i", type=Path, required=True, help="Input puzzle file (JSON)"
    )
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    args = parser.parse_args()

    input_file = args.input
    puzzle_data = load_puzzle_data(input_file)
    puzzle = KakuroPuzzle(puzzle_data["size"], puzzle_data["cells"])

    solution = solve_kakuro(puzzle)
    if solution is None:
        print(f"No solution exists for {input_file}")
        return

    solution_data = {
        "size": puzzle.size,
        "cells": puzzle_data["cells"],
        "solution_cells": [cell.__dict__ for cell in solution],
    }

    output_file = args.output or input_file.with_stem(
        input_file.stem + "_sol"
    ).with_suffix(".json")
    print(f"Writing solution to {output_file}")
    output_file.write_text(json.dumps(solution_data))


if __name__ == "__main__":
    main()
