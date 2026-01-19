"""Debug visualization for OMR grading."""

import cv2
import numpy as np
from typing import List, Tuple


def create_debug_overlay(
    original_image: np.ndarray,
    bounding_rect: Tuple[int, int, int, int],
    horizontal_separators: List[int],
    vertical_separators: List[int],
    student_answers: List[int],
    table_format: str
) -> np.ndarray:
    """
    Create debug visualization showing detected table and answers.
    
    Args:
        original_image: Original image (before perspective correction)
        bounding_rect: Bounding rectangle of table (x, y, w, h)
        horizontal_separators: Positions of horizontal separators
        vertical_separators: Positions of vertical separators
        student_answers: List of answer indices (-1 for no answer, -2 for ambiguous)
        table_format: 'columns=questions' or 'rows=questions'
        
    Returns:
        Annotated debug image
    """
    # Create a copy to draw on
    debug_image = original_image.copy()
    
    # Convert to BGR if grayscale
    if len(debug_image.shape) == 2:
        debug_image = cv2.cvtColor(debug_image, cv2.COLOR_GRAY2BGR)
    
    # Draw bounding box
    x, y, w, h = bounding_rect
    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (255, 0, 0), 3)
    
    # Draw horizontal separators
    for sep in horizontal_separators:
        cv2.line(debug_image, (x, y + sep), (x + w, y + sep), (0, 255, 0), 1)
    
    # Draw vertical separators
    for sep in vertical_separators:
        cv2.line(debug_image, (x + sep, y), (x + sep, y + h), (0, 255, 0), 1)
    
    # Draw answer highlights
    h_sep = sorted(horizontal_separators)
    v_sep = sorted(vertical_separators)
    
    answer_idx = 0
    
    if table_format == 'columns=questions':
        # Questions are columns, answers are rows
        for q_idx in range(len(v_sep) - 2):  # Exclude header and outer edge
            for a_idx in range(len(h_sep) - 2):  # Exclude header and outer edge
                if answer_idx >= len(student_answers):
                    break
                
                # Cell coordinates
                cell_x1 = x + v_sep[q_idx + 1]
                cell_y1 = y + h_sep[a_idx + 1]
                cell_x2 = x + v_sep[q_idx + 2]
                cell_y2 = y + h_sep[a_idx + 2]
                
                # Check if this cell corresponds to the student's answer
                if student_answers[answer_idx] == a_idx:
                    if student_answers[answer_idx] == -2:
                        # Ambiguous
                        cv2.rectangle(debug_image, (cell_x1, cell_y1), (cell_x2, cell_y2), (0, 0, 255), 2)
                    else:
                        # Filled
                        cv2.rectangle(debug_image, (cell_x1, cell_y1), (cell_x2, cell_y2), (0, 255, 0), 2)
                
                answer_idx += 1
    
    # Add text annotation
    cv2.putText(debug_image, "OMR Debug Overlay", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    return debug_image


def draw_cell_grid_with_answers(
    rectified_image: np.ndarray,
    horizontal_separators: List[int],
    vertical_separators: List[int],
    student_answers: List[int],
    table_format: str
) -> np.ndarray:
    """
    Draw cell grid with answer highlights on rectified image.
    
    Args:
        rectified_image: Perspective-corrected image
        horizontal_separators: Positions of horizontal separators
        vertical_separators: Positions of vertical separators
        student_answers: List of answer indices for each question
        table_format: 'columns=questions' or 'rows=questions'
        
    Returns:
        Annotated image with cell grid and answers
    """
    # Create a copy to draw on
    debug_image = rectified_image.copy()
    
    # Convert to BGR if grayscale
    if len(debug_image.shape) == 2:
        debug_image = cv2.cvtColor(debug_image, cv2.COLOR_GRAY2BGR)
    
    h_sep = sorted(horizontal_separators)
    v_sep = sorted(vertical_separators)
    
    # Draw grid
    for sep in h_sep:
        cv2.line(debug_image, (0, sep), (debug_image.shape[1], sep), (100, 100, 100), 1)
    
    for sep in v_sep:
        cv2.line(debug_image, (sep, 0), (sep, debug_image.shape[0]), (100, 100, 100), 1)
    
    # Highlight answers
    if table_format == 'columns=questions':
        # Questions are columns, answers are rows
        for q_idx, answer_idx in enumerate(student_answers):
            if answer_idx >= 0:
                y1 = h_sep[answer_idx + 1]
                y2 = h_sep[answer_idx + 2]
                x1 = v_sep[q_idx + 1]
                x2 = v_sep[q_idx + 2]
                
                if answer_idx == -2:
                    # Ambiguous - red
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                else:
                    # Filled - green
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    elif table_format == 'rows=questions':
        # Questions are rows, answers are columns
        for q_idx, answer_idx in enumerate(student_answers):
            if answer_idx >= 0:
                x1 = v_sep[answer_idx + 1]
                x2 = v_sep[answer_idx + 2]
                y1 = h_sep[q_idx + 1]
                y2 = h_sep[q_idx + 2]
                
                if answer_idx == -2:
                    # Ambiguous - red
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                else:
                    # Filled - green
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    return debug_image
