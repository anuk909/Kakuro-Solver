import argparse
import os
import random
import re
import time
import traceback

import requests
from bs4 import BeautifulSoup, Tag
from common import PUZZLE_JSON_SCHEMA, pretty_json_str
from jsonschema import validate

SOURCE = "kakuroconquest"


def get_puzzle_page(size: str, difficulty: str) -> str:
    """Get puzzle page HTML with rate limiting."""
    base_url = f"https://www.{SOURCE}.com"
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
    for y, row in enumerate(rows):
        for x, cell in enumerate(row.find_all("td")):
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

    # Find sum values in divs
    right_divs = cell.find_all("div", class_="topNumberHelp")
    down_divs = cell.find_all("div", class_="bottomNumberHelp")
    if not right_divs and not down_divs:
        if cell.find("input"):
            return None
        else:
            cell_data["wall"] = True
            return cell_data

    if right_divs:
        cell_data["right"] = int(right_divs[0].text.strip())
    if down_divs:
        cell_data["down"] = int(down_divs[0].text.strip())
    return cell_data


def save_puzzle(puzzle: dict, size: str, difficulty: str, puzzle_id: int):
    """Save puzzle to JSON file with compact formatting."""
    os.makedirs(SOURCE, exist_ok=True)
    filename = f"{SOURCE}/{size}_{difficulty}_{puzzle_id}.json"

    # Format JSON with exact spacing and indentation
    with open(filename, "w") as f:
        f.write(pretty_json_str(puzzle))

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
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape all puzzle combinations",
    )
    args = parser.parse_args()

    if not (args.all or args.size or args.difficulty):
        parser.error("Must specify either --all, --size or --difficulty")

    sizes = [args.size] if args.size else ["4x4", "6x6", "8x8", "9x11", "9x17"]
    difficulties = (
        [args.difficulty]
        if args.difficulty
        else ["easy", "intermediate", "hard", "challenging", "expert"]
    )

    failed_counter = 0
    for size in sizes:
        for difficulty in difficulties:
            for _ in range(args.count):
                try:
                    print(f"Scraping {size} {difficulty} puzzle...")
                    html = get_puzzle_page(size, difficulty)
                    puzzle_id = extract_puzzle_id(html)

                    puzzle = parse_puzzle(html)
                    validate(puzzle, PUZZLE_JSON_SCHEMA)
                    save_puzzle(puzzle, size, difficulty, puzzle_id)
                    print(f"✓ Scraped {size} {difficulty} puzzle {puzzle_id}")
                except Exception as e:
                    failed_counter += 1
                    print(f"✗ Error scraping puzzle: {e}, {traceback.print_exc()}")
                    if failed_counter > 3:
                        print("Too many failures, exiting")
                        return
                    continue

                # Additional delay between puzzles
                time.sleep(random.uniform(0.1, 0.2))


if __name__ == "__main__":
    main()
