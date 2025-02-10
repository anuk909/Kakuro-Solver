# Kakuro Solver

This project provides a Kakuro puzzle solver using the Z3 SMT solver. \
The solver can read a Kakuro puzzle from a JSON file, solve it, and output the solution in either JSON or SVG format.

## What is Kakuro?

Kakuro is a logic-based number puzzle that is often referred to as a mathematical crossword. The objective is to fill all of the blank squares in the grid with digits from 1 to 9 such that the sum of the numbers in each horizontal and vertical block matches the clue associated with that block. Additionally, no number may be used more than once in any block. For more information, you can visit [Wikipedia](https://en.wikipedia.org/wiki/Kakuro).

Kakuru puzzles comes in all shapes and sizes, this is an example for simple kakuro of 5x5:

<img src="examples/raw_puzzle_image.png" width="300">

## What is Z3?

Z3 is a high-performance theorem prover developed by Microsoft Research. It is used for checking the satisfiability of logical formulas over one or more theories. Z3 is widely used in formal verification, program analysis, and other applications that require solving complex logical problems. For more information, you can visit the [Z3 GitHub repository](https://github.com/Z3Prover/z3).

## Features

- Read Kakuro puzzles from JSON files.
- Solve Kakuro puzzles using the Z3 SMT solver.
- Output solutions in JSON or SVG format.
- Display puzzles without solving them.

## Requirements

- Python 3.11+
- `z3-solver` library

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/kakuro-solver.git
   cd kakuro-solver
   ```

2. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

The solver can be used via the command line. The following options are available:

- `--input` or `-i`: Path to the input JSON file containing the Kakuro puzzle.
- `--output` or `-o`: Path to the output file where the solution will be saved (output format deduced by suffix).
- `--mode`: Mode of operation, either `show` to display the puzzle or `solve` to solve it (default: `solve`).

### Examples

To solve a Kakuro puzzle and save the solution as an SVG file:

```sh
python kakuru_solver.py --input examples/puzzle.json --output examples/solution.svg --mode solve
```

**SVG Output:**

<img src="examples/solution.svg" width="300">

To solve a Kakuro puzzle and save the solution as a json file:

```sh
python kakuru_solver.py --input examples/puzzle.json --output examples/solution.json --mode solve
```

To display a Kakuro puzzle without solving it:

```sh
python kakuru_solver.py --input examples/puzzle.json --output examples/puzzle.svg --mode show
```

**SVG Output:**

<img src="examples/puzzle.svg" width="300">

#### Input JSON Format

The input JSON file should have the following structure:

```
{
  "size": [number_of_rows, number_of_columns],
  "cells": [
    { "x": row, "y": column, "wall": true },
    { "x": row, "y": column, "right": sum },
    { "x": row, "y": column, "down": sum },
    { "x": row, "y": column, "value": value }
  ]
}
```

- `size`: A list containing the number of rows and columns of the puzzle.
- `cells`: A list of cell definitions. Each cell can be a wall, a clue cell with a sum, or a pre-filled cell with a value. The value key is used for the JSON output too.

You can see full input files examples in [examples/puzzle.json](examples/puzzle.json) and [examples/harder_puzzle.json](examples/harder_puzzle.json)

## Contact

For any questions or feedback, please contact [anuk909@gmail.com](mailto:anuk909@gmail.com).

## Future Plans

- Write a Medium post about the program to share insights and implementation details.
- Develop an OCR module to generate JSON input files from images of Kakuro puzzles.
- Write solvers for many more kinds of puzzles.
