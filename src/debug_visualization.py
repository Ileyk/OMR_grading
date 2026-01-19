"""Debug visualization for OMR grading."""

import cv2
import numpy as np
from typing import List, Tuple, Optional


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


def create_composite_debug_image(
    rectified_image: np.ndarray,
    horizontal_separators: List[int],
    vertical_separators: List[int],
    student_answers: List[int],
    table_format: str,
    cell_margin_trim: float,
    horizontal_mask: Optional[np.ndarray] = None,
    vertical_mask: Optional[np.ndarray] = None,
    grid_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Create composite debug image showing line masks and final grid overlay.
    
    Args:
        rectified_image: Perspective-corrected color image
        horizontal_separators: Positions of horizontal separators
        vertical_separators: Positions of vertical separators
        student_answers: List of answer indices
        table_format: 'columns=questions' or 'rows=questions'
        horizontal_mask: Optional horizontal line mask from extract_line_masks
        vertical_mask: Optional vertical line mask from extract_line_masks
        grid_mask: Optional combined grid mask from extract_line_masks
        
    Returns:
        Composite debug image with masks and grid overlay
    """
    # Get cell grid with answers
    cell_grid_image = draw_cell_grid_with_answers(
        rectified_image,
        horizontal_separators,
        vertical_separators,
        student_answers,
        table_format,
        cell_margin_trim
    )
    
    # If no masks provided, just return the cell grid
    if horizontal_mask is None and vertical_mask is None and grid_mask is None:
        return cell_grid_image
    
    # Create mask visualizations (convert binary to BGR for display)
    images_to_stack = []
    
    # Add cell grid as primary image
    images_to_stack.append(cell_grid_image)
    
    # Add individual masks if provided
    if horizontal_mask is not None:
        h_mask_bgr = cv2.cvtColor(horizontal_mask, cv2.COLOR_GRAY2BGR)
        images_to_stack.append(h_mask_bgr)
    
    if vertical_mask is not None:
        v_mask_bgr = cv2.cvtColor(vertical_mask, cv2.COLOR_GRAY2BGR)
        images_to_stack.append(v_mask_bgr)
    
    if grid_mask is not None:
        grid_mask_bgr = cv2.cvtColor(grid_mask, cv2.COLOR_GRAY2BGR)
        images_to_stack.append(grid_mask_bgr)
    
    # If only one image, return it
    if len(images_to_stack) == 1:
        return images_to_stack[0]
    
    # Resize all images to the same height for stacking
    target_height = cell_grid_image.shape[0]
    resized_images = []
    
    for img in images_to_stack:
        if img.shape[0] != target_height:
            scale = target_height / img.shape[0]
            new_width = int(img.shape[1] * scale)
            resized = cv2.resize(img, (new_width, target_height))
            resized_images.append(resized)
        else:
            resized_images.append(img)
    
    # Stack images horizontally
    composite = np.hstack(resized_images)
    
    # Add labels
    label_height = 25
    composite_with_labels = np.vstack([
        np.full((label_height, composite.shape[1], 3), 255, dtype=np.uint8),
        composite
    ])
    
    # Add text labels
    labels = ["Cell Grid + Answers"]
    if horizontal_mask is not None:
        labels.append("Horizontal Lines")
    if vertical_mask is not None:
        labels.append("Vertical Lines")
    if grid_mask is not None:
        labels.append("Combined Grid")
    
    x_offset = 10
    for label in labels:
        cv2.putText(composite_with_labels, label, (x_offset, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        # Estimate width for next label (rough approximation)
        x_offset += len(label) * 50 + 20
    
    return composite_with_labels


def draw_cell_grid_with_answers(
    rectified_image: np.ndarray,
    horizontal_separators: List[int],
    vertical_separators: List[int],
    student_answers: List[int],
    table_format: str,
    cell_margin_trim: float
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
    
    # Add text annotation
    cv2.putText(debug_image, "OMR Debug - Green=Answer, Red=Ambiguous", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Highlight answers
    if table_format == 'columns=questions':
        # Questions are columns, answers are rows
        for q_idx, answer_idx in enumerate(student_answers):
            # Bounds check
            if q_idx + 2 >= len(v_sep):
                continue
            
            if answer_idx == -2:
                # Ambiguous - red (mark first answer row as indicator)
                if len(h_sep) >= 3:  # Need at least 3 separators (outer + header + first cell)
                    y1 = h_sep[0+1] + int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    # y2 = h_sep[0 + 2]
                    y2 = h_sep[-1] - int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    x1 = v_sep[q_idx + 1] + int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    x2 = v_sep[q_idx + 2] - int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
            elif answer_idx >= 0:
                # Filled - green
                if answer_idx + 2 < len(h_sep):
                    y1 = h_sep[answer_idx + 1] + int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    y2 = h_sep[answer_idx + 2] - int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    x1 = v_sep[q_idx + 1] + int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    x2 = v_sep[q_idx + 2] - int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    elif table_format == 'rows=questions':
        # Questions are rows, answers are columns
        for q_idx, answer_idx in enumerate(student_answers):
            # Bounds check
            if q_idx + 2 >= len(h_sep):
                continue
            
            if answer_idx == -2:
                # Ambiguous - red (mark first answer column as indicator)
                if len(v_sep) >= 3:  # Need at least 3 separators (outer + header + first cell)
                    x1 = v_sep[0 + 1] + int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    # x2 = v_sep[0 + 2]
                    x2 = v_sep[-1] - int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    y1 = h_sep[q_idx + 1] + int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    y2 = h_sep[q_idx + 2] - int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
            elif answer_idx >= 0:
                # Filled - green
                if answer_idx + 2 < len(v_sep):
                    x1 = v_sep[answer_idx + 1] + int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )  
                    x2 = v_sep[answer_idx + 2] - int( (v_sep[q_idx+2]-v_sep[q_idx+1]) * cell_margin_trim/100 )
                    y1 = h_sep[q_idx + 1] + int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    y2 = h_sep[q_idx + 2] - int ( (h_sep[0+1+1]-h_sep[0+1]) * cell_margin_trim/100 )
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    return debug_image
