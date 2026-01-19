"""Table detection and separator extraction for OMR grading."""

import cv2
import numpy as np
from typing import List, Tuple


def extract_separators(grid_mask: np.ndarray, axis: str = 'horizontal') -> List[int]:
    """
    Extract separator positions by summing pixels along an axis and finding peaks.
    
    Args:
        grid_mask: Binary grid mask
        axis: 'horizontal' or 'vertical'
        
    Returns:
        List of separator positions (pixel coordinates)
    """
    if axis == 'horizontal':
        # Sum along horizontal axis to get vertical positions of horizontal lines
        signal = np.sum(grid_mask, axis=1)
    elif axis == 'vertical':
        # Sum along vertical axis to get horizontal positions of vertical lines
        signal = np.sum(grid_mask, axis=0)
    else:
        raise ValueError(f"Invalid axis: {axis}")
    
    # Normalize signal
    signal = signal / np.max(signal) if np.max(signal) > 0 else signal
    
    # Apply threshold to find peaks
    threshold = 0.3  # Threshold for peak detection
    peaks = np.where(signal > threshold)[0]
    
    if len(peaks) == 0:
        raise ValueError(f"No peaks found for {axis} axis")
    
    # Merge adjacent peaks (clusters) by taking centroids
    separators = _merge_peaks(peaks)
    
    return separators


def _merge_peaks(peaks: np.ndarray, gap_threshold: int = 5) -> List[int]:
    """
    Merge adjacent peaks into single separator positions.
    
    Args:
        peaks: Array of peak positions
        gap_threshold: Maximum gap between peaks to consider them as one separator
        
    Returns:
        List of merged separator positions (centroids)
    """
    if len(peaks) == 0:
        return []
    
    separators = []
    current_cluster = [peaks[0]]
    
    for i in range(1, len(peaks)):
        if peaks[i] - peaks[i-1] <= gap_threshold:
            # Same cluster
            current_cluster.append(peaks[i])
        else:
            # New cluster - calculate centroid of current cluster
            centroid = int(np.mean(current_cluster))
            separators.append(centroid)
            current_cluster = [peaks[i]]
    
    # Don't forget the last cluster
    centroid = int(np.mean(current_cluster))
    separators.append(centroid)
    
    return separators


def validate_table_dimensions(
    horizontal_separators: List[int],
    vertical_separators: List[int],
    num_questions: int,
    num_answers: int,
    table_format: str
) -> Tuple[bool, str]:
    """
    Validate that detected separators match expected table dimensions.
    
    Args:
        horizontal_separators: List of horizontal separator positions
        vertical_separators: List of vertical separator positions
        num_questions: Number of questions
        num_answers: Number of possible answers (P)
        table_format: 'columns=questions' or 'rows=questions'
        
    Returns:
        Tuple of (is_valid, message)
    """
    num_h_sep = len(horizontal_separators)
    num_v_sep = len(vertical_separators)
    
    # Expected counts: +2 for outer edges and headers
    expected_h = num_answers + 2 if table_format == 'columns=questions' else num_questions + 2
    expected_v = num_questions + 2 if table_format == 'columns=questions' else num_answers + 2
    
    if num_h_sep != expected_h:
        return False, f"Horizontal separators mismatch: found {num_h_sep}, expected {expected_h}"
    
    if num_v_sep != expected_v:
        return False, f"Vertical separators mismatch: found {num_v_sep}, expected {expected_v}"
    
    return True, "Dimensions valid"


def extract_cell_regions(
    rectified_image: np.ndarray,
    horizontal_separators: List[int],
    vertical_separators: List[int]
) -> np.ndarray:
    """
    Extract individual cell regions from the rectified table image.
    
    Args:
        rectified_image: Perspective-corrected table image
        horizontal_separators: List of horizontal separator positions
        vertical_separators: List of vertical separator positions
        
    Returns:
        2D array of cell regions (shape: [num_rows, num_cols])
    """
    # Sort separators to ensure proper ordering
    h_sep = sorted(horizontal_separators)
    v_sep = sorted(vertical_separators)
    
    # Extract cells between separators
    cells = []
    for i in range(len(h_sep) - 1):
        row = []
        for j in range(len(v_sep) - 1):
            y1, y2 = h_sep[i], h_sep[i+1]
            x1, x2 = v_sep[j], v_sep[j+1]
            
            # Extract cell region with small padding
            cell = rectified_image[y1:y2, x1:x2]
            row.append(cell)
        cells.append(row)
    
    return np.array(cells, dtype=object)


def get_question_cells(
    cell_grid: np.ndarray,
    question_index: int,
    table_format: str
) -> np.ndarray:
    """
    Extract all answer cells for a specific question.
    
    Args:
        cell_grid: 2D array of cell regions
        question_index: Index of the question (0-based)
        table_format: 'columns=questions' or 'rows=questions'
        
    Returns:
        Array of cell images for this question's possible answers
    """
    if table_format == 'columns=questions':
        # Questions are columns, answers are rows
        # Return all rows for this column (skip header row at index 0)
        return cell_grid[1:, question_index + 1]
    elif table_format == 'rows=questions':
        # Questions are rows, answers are columns
        # Return all columns for this row (skip header column at index 0)
        return cell_grid[question_index + 1, 1:]
    else:
        raise ValueError(f"Invalid table format: {table_format}")


def detect_filled_cell(
    cell_image: np.ndarray,
    ink_threshold: float = 0.15
) -> bool:
    """
    Detect if a cell is filled by the student.
    
    Checks if the fraction of inked pixels exceeds the threshold.
    
    Args:
        cell_image: Binary cell image
        ink_threshold: Threshold for fraction of inked pixels (0-1)
        
    Returns:
        True if cell is filled, False otherwise
    """
    if cell_image.size == 0:
        return False
    
    # Count white pixels (ink) in the cell
    white_pixels = np.sum(cell_image > 128)
    total_pixels = cell_image.size
    
    ink_fraction = white_pixels / total_pixels
    
    return ink_fraction >= ink_threshold
