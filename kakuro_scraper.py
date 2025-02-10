import requests
from bs4 import BeautifulSoup, Tag
import json
import time
import random
import os
import argparse
from typing import Dict, List, Optional, Tuple
import re

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
    if not isinstance(table, Tag):
        raise ValueError("No puzzle table found")
    
    rows = list(table.find_all('tr'))
    if not rows:
        raise ValueError("No rows found in puzzle")
    
    first_row_cells = []
    first_row = rows[0]
    if isinstance(first_row, Tag):
        first_row_cells = [td for td in first_row.find_all('td') 
                          if not td.get('class') == 'spacer']
    
    if not first_row_cells:
        raise ValueError("No valid cells found in first row")
        
    height = len(rows)
    width = len(first_row_cells)
    size = [width, height]
    
    cells = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row.find_all('td')):
            if cell.get('class') == 'spacer':
                continue
            
            cell_data = parse_cell(cell, x, y)
            if cell_data:
                cells.append(cell_data)
    
    return {"size": size, "cells": cells}

def parse_cell(cell: BeautifulSoup, x: int, y: int) -> Optional[Dict]:
    """Parse individual cell into JSON format."""
    input_field = cell.find('input')
    divs = cell.find_all('div', string=re.compile(r'\d+'))
    
    if not input_field and not divs:
        return {"x": x, "y": y, "wall": True}
    
    cell_data = {"x": x, "y": y}
    
    for div in divs:
        try:
            value = int(div.text.strip())
            style = div.get('style', '')
            if 'border-left' in style:
                cell_data["right"] = value
            else:
                cell_data["down"] = value
        except ValueError:
            continue
    
    return cell_data if len(cell_data) > 2 else None

def save_puzzle(puzzle: Dict, size: str, difficulty: str, puzzle_id: int):
    """Save puzzle to JSON file."""
    os.makedirs("kakuroconquest", exist_ok=True)
    filename = f"kakuroconquest/{size}_{difficulty}_{puzzle_id}.json"
    
    class KakuroJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, dict):
                ordered = {}
                for key in ["x", "y", "wall", "right", "down"]:
                    if key in obj:
                        ordered[key] = obj[key]
                return ordered
            return super().default(obj)
    
    formatted_json = json.dumps(puzzle, indent=2, cls=KakuroJSONEncoder)
    formatted_json = re.sub(r'\[\n\s+(\d+),\n\s+(\d+)\n\s+\]', 
                           r'[\1, \2]', formatted_json)
    
    with open(filename, 'w') as f:
        f.write(formatted_json)
        f.write('\n')

def main():
    """Main function to scrape puzzles."""
    parser = argparse.ArgumentParser(description="Kakuro Puzzle Scraper")
    parser.add_argument("--size", choices=["4x4", "6x6", "8x8", "9x11", "9x17"])
    parser.add_argument("--difficulty", 
                       choices=["easy", "intermediate", "hard", "challenging", "expert"])
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()

    sizes = [args.size] if args.size else ["4x4", "6x6", "8x8", "9x11", "9x17"]
    difficulties = [args.difficulty] if args.difficulty else ["easy", "intermediate", 
                   "hard", "challenging", "expert"]
    
    for size in sizes:
        for difficulty in difficulties:
            for _ in range(args.count):
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
                    print(f"✗ Error scraping puzzle: {e}")
                    continue
                
                time.sleep(random.uniform(0.1, 0.2))

if __name__ == "__main__":
    main()
