import json
import argparse

import cv2
import numpy as np
import easyocr
from pathlib import Path
from typing import Any
from tqdm import tqdm


def detect_grid_lines(img: np.ndarray) -> tuple[list[int], list[int]]:
    """
    Detect horizontal and vertical grid lines in the image.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Find lines using HoughLines
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    if lines is None:
        raise ValueError("Could not detect grid lines")

    vertical_lines: list[int] = []
    horizontal_lines: list[int] = []

    for line in lines[:, 0]:
        rho, theta = line
        if abs(theta) < 0.1 or abs(theta - np.pi) < 0.1:  # Vertical lines
            vertical_lines.append(int(abs(rho)))
        elif abs(theta - np.pi / 2) < 0.1:  # Horizontal lines
            horizontal_lines.append(int(abs(rho)))

    def merge_lines(lines: list[int], tolerance: int = 10) -> list[int]:
        """
        Merge lines that are close together.
        """
        if not lines:
            return []
        lines_sorted = sorted(lines)
        merged = [lines_sorted[0]]
        for line in lines_sorted[1:]:
            if line - merged[-1] > tolerance:
                merged.append(line)
        return merged

    return (merge_lines(vertical_lines), merge_lines(horizontal_lines))


def extract_number_from_quadrant(
    reader: easyocr.Reader, cell: np.ndarray, quadrant: str
) -> int | None:
    """
    Extract number from a specific quadrant of the cell.
    """
    h, w = cell.shape

    # Select region of interest based on quadrant
    if quadrant == "right":
        roi = cell[0 : h // 2, w // 3 :]  # Take more of the right side
    else:  # down
        roi = cell[h // 3 :, 0 : w // 2]  # Take more of the bottom

    # Upscale for better OCR
    roi = cv2.resize(roi, (200, 200), interpolation=cv2.INTER_CUBIC)

    # Enhanced preprocessing
    roi = cv2.fastNlMeansDenoising(roi)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    roi = clahe.apply(roi)
    roi = cv2.GaussianBlur(roi, (3, 3), 0)

    # Attempt to read text
    results = reader.readtext(roi, allowlist="0123456789")
    for _, text, conf in results:
        if text and text.isdigit() and conf > 0.3:
            number = int(text)
            if number < 100:  # Validate number is reasonable
                return number

    return None


def is_clue(cell: np.ndarray) -> bool:
    """Determine if a cell contains a clue based on pixel intensity.

    Args:
        cell (np.ndarray): Cell image

    Returns:
        bool: True if the cell appears to be a clue, False otherwise
    """
    return np.mean(cell) < 200


def process_kakuro_image(image_path: Path) -> Any:
    """Process a Kakuro puzzle image and extract clue information.

    Args:
        image_path (str): Path to the image file

    Returns:
        Dict containing puzzle size and cell information
    """
    # Initialize EasyOCR
    reader = easyocr.Reader(["en"], gpu=False)

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Detect grid lines
    vertical_lines, horizontal_lines = detect_grid_lines(img)
    rows = len(horizontal_lines) - 1
    cols = len(vertical_lines) - 1
    print(f"Detected grid size: {rows}x{cols}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Process cells
    clue_cells = []

    for x in tqdm(range(cols), desc="Processing columns"):
        for y in tqdm(range(rows), desc=f"Processing cells in column {x}", leave=False):            # Extract cell
            cell = gray[
                horizontal_lines[y] + 2 : horizontal_lines[y + 1] + 2,
                vertical_lines[x] + 2 : vertical_lines[x + 1] + 2,
            ]

            if not is_clue(cell):
                continue

            cell_data = {"x": x, "y": y}

            if right_number := extract_number_from_quadrant(reader, cell, "right"):
                cell_data["right"] = right_number

            if down_number := extract_number_from_quadrant(reader, cell, "down"):
                cell_data["down"] = down_number

            if not (right_number or down_number):
                cell_data["wall"] = True
            clue_cells.append(cell_data)

    # Sort cells by position
    clue_cells.sort(key=lambda c: (c["x"], c["y"]))
    return {"size": [rows, cols], "cells": clue_cells}


def main() -> None:
    """Main function to parse arguments and process Kakuro puzzle image."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process a Kakuro puzzle image and write it to json"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to the input Kakuro puzzle image",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to the output JSON file (optional)",
    )
    args = parser.parse_args()

    input_file = args.input

    result = process_kakuro_image(input_file)

    output_file = args.output or input_file.with_stem(
        input_file.stem + "_ocr"
    ).with_suffix(".json")
    print(f"Writing OCR json to {output_file}")
    output_file.write_text(json.dumps(result))


if __name__ == "__main__":
    main()
