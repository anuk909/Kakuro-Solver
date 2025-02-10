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

    # Check if it's a wall cell (no input field and no sums)
    if not cell.find("input") and not cell.find_all("div", string=re.compile(r"\d+")):
        return {"x": x, "y": y, "wall": True}

    # Find sum values in divs
    divs = cell.find_all("div", string=re.compile(r"\d+"))
    if not divs:
        # Check for solution value
        input_field = cell.find("input")
        if isinstance(input_field, Tag):
            value_str = input_field.get("value")
            if value_str and isinstance(value_str, str):
                try:
                    value = int(value_str.strip())
                    if 1 <= value <= 9:  # Only include valid values
                        return {"x": x, "y": y, "value": value}
                except (ValueError, TypeError):
                    pass
        return None  # Empty cell or invalid value

    # Parse sums - first div is usually right sum, second is down sum
    for i, div in enumerate(divs):
        try:
            value = int(div.text.strip())
            if i == 0 and len(divs) == 1:  # Single sum - check position
                if div.get("style", "").find("border-left") >= 0:
                    cell_data["right"] = value
                else:
                    cell_data["down"] = value
            elif i == 0:  # First of multiple sums
                cell_data["right"] = value
            else:
                cell_data["down"] = value
        except ValueError:
            continue
    return cell_data if len(cell_data) > 2 else None


def save_puzzle(puzzle: dict, size: str, difficulty: str, puzzle_id: int):
    """Save puzzle to JSON file with compact formatting."""
    # Ensure cells are sorted correctly: wall, clue (right/down), solution
    puzzle["cells"]

    # Create kakuroconquest directory if it doesn't exist
    os.makedirs("kakuroconquest", exist_ok=True)

    filename = f"kakuroconquest/{size}_{difficulty}_{puzzle_id}.json"

    # Save with compact JSON formatting
    with open(filename, "w") as f:
        json.dump(puzzle, f, separators=(",", ":"))

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
