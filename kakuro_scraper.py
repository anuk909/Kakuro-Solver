import requests
from bs4 import BeautifulSoup, Tag
import json
import time
import random
import os
import argparse
from typing import Dict, List, Optional, Tuple
import re
from common import validate_puzzle_data

def solve_puzzle(size: str, difficulty: str, puzzle_id: int) -> Dict[str, int]:
    """Submit solution request and parse response."""
    base_url = "https://www.kakuroconquest.com"
    url = f"{base_url}/{size}/{difficulty}/{puzzle_id}"
    
    try:
        # Get puzzle page to find solution form
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse form and submit solution request
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', {'name': 'puzzle'})
        if not isinstance(form, Tag):
            raise ValueError("No puzzle form found")
            
        # Extract solution values
        solution_data = {}
        for input_field in form.find_all('input'):
            if not isinstance(input_field, Tag):
                continue
            name = input_field.get('name')
            if isinstance(name, str) and name.startswith('cell_'):
                solution_data[name] = ''  # Empty value to request solution
        
        if not solution_data:
            raise ValueError("No input cells found in puzzle form")
            
        # Submit form to get solution
        print(f"Requesting solution for puzzle {puzzle_id}...")
        response = requests.post(url, data=solution_data, timeout=10)
        response.raise_for_status()
        
        # Parse solution from response
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', {'name': 'puzzle'})
        if not isinstance(form, Tag):
            raise ValueError("No solution form found in response")
            
        # Extract solution values
        solution_values = {}
        for input_field in form.find_all('input'):
            if not isinstance(input_field, Tag):
                continue
            name = input_field.get('name')
            value = input_field.get('value')
            if (isinstance(name, str) and name.startswith('cell_') and 
                isinstance(value, str) and value.strip().isdigit()):
                solution_values[name] = int(value.strip())
        
        if not solution_values:
            raise ValueError("No solution values found in response")
            
        return solution_values
        
    except requests.Timeout:
        raise ValueError(f"Request timed out for {url}")
    except requests.RequestException as e:
        raise ValueError(f"Failed to get solution: {e}")

def get_puzzle_page(size: str, difficulty: str, puzzle_id: Optional[int] = None) -> str:
    """Get puzzle page HTML with rate limiting."""
    base_url = "https://www.kakuroconquest.com"
    url = f"{base_url}/{size}/{difficulty}"
    if puzzle_id:
        url += f"/{puzzle_id}"
    
    # Respect rate limits with random delay
    time.sleep(random.uniform(2.0, 4.0))
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.Timeout:
        raise ValueError(f"Request timed out for {url}")
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch {url}: {e}")

def extract_puzzle_info(html: str, base_url: str) -> tuple[Optional[int], Optional[str]]:
    """Extract puzzle ID and URL from the page HTML."""
    # Extract puzzle ID
    id_match = re.search(r'puzzle (\d+)', html)
    puzzle_id = int(id_match.group(1)) if id_match else None
    
    # Extract canonical URL
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.find('link', rel='canonical')
    if isinstance(canonical, Tag):
        url = canonical.get('href')
        if isinstance(url, str):
            return puzzle_id, url
    
    # Fallback: look for og:url
    og_url = soup.find('meta', property='og:url')
    if isinstance(og_url, Tag):
        url = og_url.get('content')
        if isinstance(url, str):
            return puzzle_id, url
            
    return puzzle_id, None

def sort_cells(cells: List[Dict]) -> List[Dict]:
    """Sort cells in order: wall cells, clue cells (right/down), then solution cells."""
    def cell_sort_key(cell: Dict) -> Tuple[int, int, int]:
        # Key order: type (wall=0, clue=1, solution=2), x, y
        if "wall" in cell:
            type_key = 0
        elif "right" in cell or "down" in cell:
            type_key = 1
        else:
            type_key = 2
        return (type_key, cell["x"], cell["y"])
    
    return sorted(cells, key=cell_sort_key)

def parse_puzzle(html: str) -> Dict:
    """Parse puzzle HTML into JSON format."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table or not isinstance(table, Tag):
        raise ValueError("No puzzle table found")
    
    # Get puzzle size from table dimensions
    rows = list(table.find_all('tr'))
    if not rows:
        raise ValueError("No rows found in puzzle")
    
    # Get all non-spacer cells from first row to determine width
    first_row_cells = []
    first_row = rows[0]
    if isinstance(first_row, Tag):
        first_row_cells = [td for td in first_row.find_all('td') if not td.get('class') == 'spacer']
    
    if not first_row_cells:
        raise ValueError("No valid cells found in first row")
        
    height = len(rows)
    width = len(first_row_cells)
    size = [width, height]  # x = width, y = height
    
    # Parse cells using y,x coordinates to match example format
    cells = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row.find_all('td')):
            # Skip spacer cells
            if cell.get('class') == 'spacer':
                continue
            
            cell_data = parse_cell(cell, x, y)
            if cell_data:
                cells.append(cell_data)
    
    # Sort cells in correct order: wall, clue (right/down), solution
    cells = sort_cells(cells)
    
    return {
        "size": size,
        "cells": cells
    }

def parse_cell(cell: BeautifulSoup, x: int, y: int) -> Optional[Dict]:
    """Parse individual cell into JSON format."""
    # Only include non-empty cells
    input_field = cell.find('input')
    divs = cell.find_all('div', string=re.compile(r'\d+'))
    
    # Empty cell (not wall, no clues)
    if input_field and not divs:
        return None
        
    # Wall cell (no input, no clues)
    if not input_field and not divs:
        return {"x": x, "y": y, "wall": True}
    
    cell_data = {"x": x, "y": y}
    
    # Parse clue values
    for div in divs:
        try:
            value = int(div.text.strip())
            # Check div style for right/down clue
            style = div.get('style', '')
            if 'border-left' in style:
                cell_data["right"] = value
            else:
                cell_data["down"] = value
        except ValueError:
            continue
            
    # Check for solution value
    if input_field and isinstance(input_field, Tag):
        value_str = input_field.get('value')
        if value_str and isinstance(value_str, str):
            try:
                value = int(value_str.strip())
                if 1 <= value <= 9:  # Only include valid values
                    cell_data["value"] = value
            except (ValueError, TypeError):
                pass
    
    return cell_data if len(cell_data) > 2 else None

def save_puzzle(puzzle: Dict, size: str, difficulty: str, puzzle_id: int, puzzle_url: str):
    """Save puzzle to JSON file with compact formatting."""
    # Add URL to puzzle data
    puzzle["url"] = puzzle_url
    
    # Create kakuroconquest directory if it doesn't exist
    os.makedirs("kakuroconquest", exist_ok=True)
    
    # Use puzzle ID in filename to avoid duplicates
    filename = f"kakuroconquest/{size}_{difficulty}_{puzzle_id}.json"
    
    # Sort cells by type and coordinates
    sorted_cells = []
    for cell in sort_cells(puzzle["cells"]):
        ordered = {}
        # Order: x, y, wall, right, down, value
        for key in ["x", "y", "wall", "right", "down", "value"]:
            if key in cell:
                ordered[key] = cell[key]
        sorted_cells.append(ordered)
    
    puzzle["cells"] = sorted_cells
    
    # Format JSON with proper indentation and array style
    class KakuroJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, dict):
                # Maintain specific order for cell properties
                if all(k in ["x", "y", "wall", "right", "down", "value"] for k in obj.keys()):
                    ordered = {}
                    for key in ["x", "y", "wall", "right", "down", "value"]:
                        if key in obj:
                            ordered[key] = obj[key]
                    return ordered
            return super().default(obj)
    
    # Format JSON with proper indentation and array style
    formatted_json = json.dumps(puzzle, indent=2, cls=KakuroJSONEncoder)
    # Fix array formatting to be on one line
    formatted_json = re.sub(r'\[\n\s+(\d+),\n\s+(\d+)\n\s+\]', r'[\1, \2]', formatted_json)
    
    with open(filename, 'w') as f:
        f.write(formatted_json)
        f.write('\n')
    
    print(f"Saved puzzle to {filename}")

def main():
    """Main function to scrape puzzles."""
    parser = argparse.ArgumentParser(description="Kakuro Puzzle Scraper")
    parser.add_argument("--size", choices=["4x4", "6x6", "8x8", "9x11", "9x17"], help="Puzzle size to scrape")
    parser.add_argument("--difficulty", choices=["easy", "intermediate", "hard", "challenging", "expert"], help="Difficulty level to scrape")
    parser.add_argument("--count", type=int, default=1, help="Number of puzzles to scrape per combination")
    args = parser.parse_args()

    sizes = [args.size] if args.size else ["4x4", "6x6", "8x8", "9x11", "9x17"]
    difficulties = [args.difficulty] if args.difficulty else ["easy", "intermediate", "hard", "challenging", "expert"]
    
    for size in sizes:
        for difficulty in difficulties:
            for _ in range(args.count):
                try:
                    print(f"Scraping {size} {difficulty} puzzle...")
                    html = get_puzzle_page(size, difficulty)
                    base_url = "https://www.kakuroconquest.com"
                    puzzle_id, puzzle_url = extract_puzzle_info(html, base_url)
                    if not puzzle_id or not puzzle_url:
                        print(f"Could not extract puzzle info for {size} {difficulty}")
                        continue
                    
                    # Solve the puzzle to get solution values
                    try:
                        solve_puzzle(size, difficulty, puzzle_id)
                        html = get_puzzle_page(size, difficulty, puzzle_id)
                    except Exception as e:
                        print(f"✗ Could not solve puzzle: {e}")
                        continue
                        
                    puzzle = parse_puzzle(html)
                    is_valid, error = validate_puzzle_data(puzzle)
                    if not is_valid:
                        print(f"✗ Invalid puzzle data: {error}")
                        continue
                        
                    save_puzzle(puzzle, size, difficulty, puzzle_id, puzzle_url)
                    print(f"✓ Scraped {size} {difficulty} puzzle {puzzle_id}")
                except Exception as e:
                    print(f"✗ Error scraping puzzle: {e}")
                    continue
                
                # Additional delay between puzzles
                time.sleep(random.uniform(2.0, 4.0))

if __name__ == "__main__":
    main()
