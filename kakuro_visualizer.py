import json
import argparse
from pathlib import Path
from common import KakuroPuzzle, SolutionCell, Solution, load_puzzle_data


def create_svg(puzzle: KakuroPuzzle, solution: Solution) -> str:
    """Create SVG representation of the puzzle/solution"""
    cell_size = 60
    rows, cols = puzzle.size
    width = cols * cell_size
    height = rows * cell_size

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background-color: white;">',
        "<style>",
        ".grid-line { stroke: #000; stroke-width: 1; }",
        ".wall { fill: #c0c0c0; stroke: #000; stroke-width: 1; }",
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
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" class="wall"/>'
                )
                svg_lines.append(
                    f'<line x1="{x}" y1="{y}" x2="{x+cell_size}" y2="{y+cell_size}" class="grid-line"/>'
                )

                if row_sum := clue.row_sum:
                    svg_lines.append(
                        f'<text x="{x+cell_size-20}" y="{y+20}" class="clue-text">{row_sum}</text>'
                    )
                if col_sum := clue.col_sum:
                    svg_lines.append(
                        f'<text x="{x+10}" y="{y+cell_size-10}" class="clue-text">{col_sum}</text>'
                    )
            else:
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" class="blank"/>'
                )

        if solution:
            for cell in solution:
                svg_lines.append(
                    f'<text x="{cell.x * cell_size + cell_size/2}" y="{cell.y * cell_size + cell_size/2 + 5}" class="solution">{cell.value}</text>'
                )

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Kakuro Puzzle Visualizer")
    parser.add_argument(
        "--input", "-i", type=Path, required=True, help="Input puzzle file (JSON)"
    )
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    args = parser.parse_args()

    puzzle_data = load_puzzle_data(args.input)
    size: tuple[int, int] = (puzzle_data["size"][0], puzzle_data["size"][1])
    puzzle = KakuroPuzzle(size, puzzle_data["cells"])
    solution: Solution = []
    if "solution_cells" in puzzle_data:
        solution = [SolutionCell(**cell) for cell in puzzle_data["solution_cells"]]

    output_file = args.output or args.input.with_suffix(".svg")
    print(f"Writing SVG to {output_file}")
    output_file.write_text(create_svg(puzzle, solution))


if __name__ == "__main__":
    main()
