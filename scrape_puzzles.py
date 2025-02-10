import requests
from bs4 import BeautifulSoup
import json
import time
import random
from typing import Dict, List, Optional, Tuple
import re

def get_puzzle_page(size: str, difficulty: str, puzzle_id: Optional[int] = None) -> str:
    """Get puzzle page HTML with rate limiting."""
    base_url = "https://www.kakuroconquest.com"
    url = f"{base_url}/{size}/{difficulty}"
    if puzzle_id:
        url += f"/{puzzle_id}"
    
    # Respect rate limits with random delay
    time.sleep(random.uniform(2.0, 4.0))
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_puzzle_id(html: str) -> Optional[int]:
    """Extract puzzle ID from the page HTML."""
    match = re.search(r'puzzle (\d+)', html)
    if match:
        return int(match.group(1))
    return None

def parse_puzzle(html: str) -> Dict:
    """Parse puzzle HTML into JSON format."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        raise ValueError("No puzzle table found")
    
    # Get puzzle size from table dimensions
    rows = table.find_all('tr')
    if not rows:
        raise ValueError("No rows found in puzzle")
    
    # Get all non-spacer cells from first row to determine width
    first_row_cells = []
    if rows[0]:
        first_row_cells = [td for td in rows[0].find_all('td') if not td.get('class') == 'spacer']
    
    if not first_row_cells:
        raise ValueError("No valid cells found in first row")
        
    size = [len(rows), len(first_row_cells)]
    
    # Parse cells
    cells = []
    for x, row in enumerate(rows):
        for y, cell in enumerate(row.find_all('td')):
            # Skip spacer cells
            if cell.get('class') == 'spacer':
                continue
            
            cell_data = parse_cell(cell, x, y)
            if cell_data:
                cells.append(cell_data)
    
    return {
        "size": size,
        "cells": cells
    }

def parse_cell(cell: BeautifulSoup, x: int, y: int) -> Optional[Dict]:
    """Parse individual cell into JSON format."""
    cell_data = {"x": x, "y": y}
    
    # Check if it's a wall cell (no input field and no sums)
    if not cell.find('input') and not cell.find_all('div', string=re.compile(r'\d+')):
        return {"x": x, "y": y, "wall": True}
    
    # Find sum values in divs
    divs = cell.find_all('div', string=re.compile(r'\d+'))
    if not divs:
        return None  # Empty cell to be filled in
        
    # Parse sums - first div is usually right sum, second is down sum
    for i, div in enumerate(divs):
        try:
            value = int(div.text.strip())
            if i == 0 and len(divs) == 1:  # Single sum - check position
                if div.get('style', '').find('border-left') >= 0:
                    cell_data["right"] = value
                else:
                    cell_data["down"] = value
            elif i == 0:  # First of multiple sums
                cell_data["right"] = value
            else:  # Second sum
                cell_data["down"] = value
        except ValueError:
            continue
    
    return cell_data if len(cell_data) > 2 else None

def save_puzzle(puzzle: Dict, size: str, difficulty: str, puzzle_id: int):
    """Save puzzle to JSON file."""
    filename = f"examples/scraped_{size}_{difficulty}_{puzzle_id}.json"
    with open(filename, 'w') as f:
        json.dump(puzzle, f, indent=2)

def main():
    """Main function to scrape puzzles."""
    sizes = ["4x4", "6x6", "8x8", "9x11", "9x17"]
    difficulties = ["easy", "intermediate", "hard", "challenging", "expert"]
    
    # Start with one puzzle per combination to test
    for size in sizes:
        for difficulty in difficulties:
            try:
                print(f"Scraping {size} {difficulty} puzzle...")
                html = get_puzzle_page(size, difficulty)
                puzzle_id = extract_puzzle_id(html)
                if not puzzle_id:
                    print(f"Could not extract puzzle ID for {size} {difficulty}")
                    continue
                    
                puzzle = parse_puzzle(html)
                save_puzzle(puzzle, size, difficulty, puzzle_id)
                print(f"✓ Scraped {size} {difficulty} puzzle {puzzle_id}")
            except Exception as e:
                print(f"✗ Error scraping {size} {difficulty}: {e}")
            
            # Additional delay between combinations
            time.sleep(random.uniform(1.0, 2.0))

if __name__ == "__main__":
    main()
