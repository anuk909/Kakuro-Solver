import argparse
import json
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup, Tag
from common import validate_puzzle_data


def get_puzzle_page(size: str, difficulty: str) -> str:
    """Get puzzle page HTML with rate limiting."""
    base_url = "https://www.kakuroconquest.com"
    url = f"{base_url}/{size}/{difficulty}"

    # Respect rate limits with random delay
    time.sleep(random.uniform(0.1, 0.2))
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.Timeout:
        raise ValueError(f"Request timed out for {url}")
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch {url}: {e}")


def extract_puzzle_id(html: str) -> int | None:
    """Extract puzzle ID from the page HTML."""
    match = re.search(r"puzzle (\d+)", html)
    if match:
        return int(match.group(1))
    return None


def parse_puzzle(html: str) -> dict:
    """Parse puzzle HTML into JSON format."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table or not isinstance(table, Tag):
        raise ValueError("No puzzle table found")

    # Get puzzle size from table dimensions
    rows = list(table.find_all("tr"))
    if not rows:
        raise ValueError("No rows found in puzzle")

    # Get all non-spacer cells from first row to determine width
    first_row_cells = []
    first_row = rows[0]
    if isinstance(first_row, Tag):
        first_row_cells = [
            td for td in first_row.find_all("td") if not td.get("class") == "spacer"
        ]

    if not first_row_cells:
        raise ValueError("No valid cells found in first row")

    size = [len(rows), len(first_row_cells)]

    # Parse cells
    cells = []
    for x, row in enumerate(rows):
        for y, cell in enumerate(row.find_all("td")):
            # Skip spacer cells
            if cell.get("class") == "spacer":
                continue

            cell_data = parse_cell(cell, x, y)
            if cell_data:
                cells.append(cell_data)

    return {"size": size, "cells": cells}


def parse_cell(cell: BeautifulSoup, x: int, y: int) -> dict | None:
    """Parse individual cell into JSON format."""
    cell_data = {"x": x, "y": y}

    # Check if it's a wall cell (empty or no divs)
    divs = cell.find_all("div")
    if not divs:
        return {"x": x, "y": y, "wall": True}

    # Find sum values using class-based identification
    for div in divs:
        if not isinstance(div, Tag):
            continue
            
        try:
            value = int(div.text.strip())
            classes = div.get("class", [])
            if isinstance(classes, list) and "bottomNumberHelp" in classes:
                cell_data["right"] = value
            elif isinstance(classes, list) and "topNumberHelp" in classes:
                cell_data["down"] = value
        except (ValueError, TypeError):
            continue

    # Only return cells with clues or wall
    return cell_data if len(cell_data) > 2 or cell_data.get("wall") else None


def save_puzzle(puzzle: dict, size: str, difficulty: str, puzzle_id: int | None):
    """Save puzzle to JSON file with compact formatting."""
    if puzzle_id is None:
        raise ValueError("Missing puzzle ID")

    # Sort cells to match example order: wall cells first, then clues
    puzzle["cells"].sort(key=lambda c: (
        not c.get("wall", False),  # Wall cells first
        c.get("x", 0),            # Then by x coordinate
        c.get("y", 0)             # Then by y coordinate
    ))

    # Format cells with exact property order
    formatted_cells = []
    for cell in puzzle["cells"]:
        ordered = {}
        # Maintain exact property order
        for key in ["x", "y", "wall", "right", "down"]:
            if key in cell:
                ordered[key] = cell[key]
        formatted_cells.append(ordered)

    # Create formatted puzzle with exact structure
    formatted_puzzle = {
        "size": puzzle["size"],
        "cells": formatted_cells
    }

    # Create kakuroconquest directory if it doesn't exist
    os.makedirs("kakuroconquest", exist_ok=True)

    filename = f"kakuroconquest/{size}_{difficulty}_{puzzle_id}.json"

    # Format JSON with exact spacing and indentation
    with open(filename, "w") as f:
        # Format size array on one line with proper spacing
        size_str = f'[{formatted_puzzle["size"][0]}, {formatted_puzzle["size"][1]}]'
        
        # Format each cell object on one line with proper spacing
        cells_str = []
        for cell in formatted_cells:
            parts = []
            for key in ["x", "y", "wall", "right", "down"]:
                if key in cell:
                    value = cell[key]
                    if isinstance(value, bool):
                        parts.append(f'"{key}": {str(value).lower()}')
                    else:
                        parts.append(f'"{key}": {value}')
            cell_str = "{ " + ", ".join(parts) + " }"
            cells_str.append("    " + cell_str)
        
        # Build final JSON string with exact formatting
        json_str = "{\n"
        json_str += f'  "size": {size_str},\n'
        json_str += '  "cells": [\n'
        json_str += ",\n".join(cells_str)
        json_str += "\n  ]\n"
        json_str += "}"  # No trailing newline to match example
        f.write(json_str)

    print(f"Saved puzzle to {filename}")


def main():
    """Main function to scrape puzzles."""
    parser = argparse.ArgumentParser(description="Kakuro Puzzle Scraper")
    parser.add_argument(
        "--size",
        choices=["4x4", "6x6", "8x8", "9x11", "9x17"],
        help="Puzzle size to scrape",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "intermediate", "hard", "challenging", "expert"],
        help="Difficulty level to scrape",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of puzzles to scrape per combination",
    )
    args = parser.parse_args()

    sizes = [args.size] if args.size else ["4x4", "6x6", "8x8", "9x11", "9x17"]
    difficulties = (
        [args.difficulty]
        if args.difficulty
        else ["easy", "intermediate", "hard", "challenging", "expert"]
    )

    for size in sizes:
        for difficulty in difficulties:
            for _ in range(args.count):
                try:
                    print(f"Scraping {size} {difficulty} puzzle...")
                    html = get_puzzle_page(size, difficulty)
                    puzzle_id = extract_puzzle_id(html)

                    puzzle = parse_puzzle(html)
                    is_valid, error = validate_puzzle_data(puzzle)
                    if not is_valid:
                        print(f"✗ Invalid puzzle data: {error}")
                        continue

                    save_puzzle(puzzle, size, difficulty, puzzle_id)
                    print(f"✓ Scraped {size} {difficulty} puzzle {puzzle_id}")
                except Exception as e:
                    print(f"✗ Error scraping puzzle: {e}")
                    continue

                # Additional delay between puzzles
                time.sleep(random.uniform(0.1, 0.2))


if __name__ == "__main__":
    main()
