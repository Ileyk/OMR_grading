"""Table detection and separator extraction for OMR grading."""

import cv2
import numpy as np
from typing import List, Tuple


def extract_separators(
    grid_mask: np.ndarray, 
    axis: str = 'horizontal',
    num_questions: int = None,
    num_answers: int = None,
    table_format: str = None
) -> List[int]:
    """
    Extract separator positions using uniform spacing assumption.
    
    Assumes separators are uniformly spaced. Uses table dimensions to estimate
    spacing and find separators at regular intervals.
    
    Args:
        grid_mask: Binary grid mask
        axis: 'horizontal' or 'vertical'
        num_questions: Number of questions
        num_answers: Number of possible answers
        table_format: 'columns=questions' or 'rows=questions'
        
    Returns:
        List of separator positions (pixel coordinates)
    """
    if axis == 'horizontal':
        # Sum along horizontal axis to get vertical positions of horizontal lines
        signal = np.sum(grid_mask, axis=1)
        size = grid_mask.shape[0]
    elif axis == 'vertical':
        # Sum along vertical axis to get horizontal positions of vertical lines
        signal = np.sum(grid_mask, axis=0)
        size = grid_mask.shape[1]
    else:
        raise ValueError(f"Invalid axis: {axis}")

    # Normalize signal
    signal = signal / np.max(signal) if np.max(signal) > 0 else signal
    
    # If table dimensions provided, use uniform spacing
    if num_questions and num_answers and table_format:
        separators = _extract_separators_uniform_spacing(
            signal, size, axis, num_questions, num_answers, table_format
        )
    else:
        # Fallback to peak detection
        separators = _extract_separators_peak_detection(signal)
    
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


def _extract_separators_uniform_spacing(
    signal: np.ndarray,
    size: int,
    axis: str,
    num_questions: int,
    num_answers: int,
    table_format: str
) -> List[int]:
    """
    Extract separators assuming uniform spacing based on table dimensions.
    
    Calculates expected number of separators and spacing, then finds peak positions
    near expected locations using a sliding window approach.
    
    Args:
        signal: 1D intensity signal (normalized)
        size: Size of the signal (image dimension along axis)
        axis: 'horizontal' or 'vertical'
        num_questions: Number of questions
        num_answers: Number of possible answers
        table_format: 'columns=questions' or 'rows=questions'
        
    Returns:
        List of separator positions
    """
    # Determine expected number of separators
    if axis == 'horizontal':
        if table_format == 'columns=questions':
            expected_count = num_answers + 2  # P answers + header + bottom edge
        else:
            expected_count = num_questions + 2  # Q questions + header + bottom edge
    else:  # vertical
        if table_format == 'columns=questions':
            expected_count = num_questions + 2  # Q questions + left edge + right edge
        else:
            expected_count = num_answers + 2  # P answers + left edge + right edge
    
    # Estimate expected spacing
    expected_spacing = size / (expected_count - 1)
    
    # For each expected position, find the nearest peak
    separators = []
    window_size = int(expected_spacing * 0.4)  # Search window: ±40% of spacing
    
    for i in range(expected_count):
        expected_pos = i * expected_spacing
        search_start = max(0, int(expected_pos - window_size))
        search_end = min(size, int(expected_pos + window_size))
        
        # Find the position with maximum signal in this window
        if search_start < search_end:
            window_signal = signal[search_start:search_end]
            local_max_idx = np.argmax(window_signal)
            peak_pos = search_start + local_max_idx
            separators.append(peak_pos)
    
    return separators


def _extract_separators_peak_detection(signal: np.ndarray) -> List[int]:
    """
    Extract separators using peak detection on the signal.
    
    Fallback method when table dimensions are not provided.
    
    Args:
        signal: 1D intensity signal (normalized)
        
    Returns:
        List of separator positions
    """
    # Apply threshold to find peaks
    threshold = 0.3
    peaks = np.where(signal > threshold)[0]
    
    if len(peaks) == 0:
        raise ValueError("No peaks found in signal - grid mask may be empty")
    
    # Merge adjacent peaks (clusters) by taking centroids
    separators = _merge_peaks(peaks)
    
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
