"""Main OMR grading pipeline."""

import os
import cv2
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from pathlib import Path

from src.image_preprocessing import (
    preprocess_image,
    extract_line_masks,
    find_table_bounding_box,
    detect_corner_points,
    perspective_correction
)
from src.table_detection import (
    extract_separators,
    validate_table_dimensions,
    extract_cell_regions,
    get_question_cells,
    detect_filled_cell,
    trim_cell_borders
)
from src.grading import GradingRule, StudentResult, grade_student_answers
from src.debug_visualization import draw_cell_grid_with_answers, create_composite_debug_image


class OMRGrader:
    """Main OMR grading system."""
    
    def __init__(
        self,
        correct_answers: List[int],
        num_questions: int,
        num_answers: int,
        table_format: str,
        grading_rule: GradingRule,
        output_dir: str = "./outputs",
        debug_dir: str = "./outputs/debug_images"
    ):
        """
        Initialize OMR grader.
        
        Args:
            correct_answers: List of correct answer indices (0-based)
            num_questions: Number of questions
            num_answers: Number of possible answers (P)
            table_format: 'columns=questions' or 'rows=questions'
            grading_rule: GradingRule object
            output_dir: Output directory for results
            debug_dir: Directory for debug images
        """
        self.correct_answers = correct_answers
        self.num_questions = num_questions
        self.num_answers = num_answers
        self.table_format = table_format
        self.grading_rule = grading_rule
        self.output_dir = output_dir
        self.debug_dir = debug_dir
        
        # Create output directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)
        
        # Validate configuration
        if len(correct_answers) != num_questions:
            raise ValueError(f"Number of correct answers ({len(correct_answers)}) doesn't match num_questions ({num_questions})")
        
        if table_format not in ['columns=questions', 'rows=questions']:
            raise ValueError(f"Invalid table format: {table_format}")
    
    def process_student_page(self, image: np.ndarray, student_id: str, cell_margin_trim: float) -> StudentResult:
        """
        Process a single student's answer sheet page.
        
        Args:
            image: Image of the student's page
            student_id: Identifier for the student
            
        Returns:
            StudentResult object
        """
        result = StudentResult(student_id)
        
        try:
            # Step 2.1: Detect table edges and perspective correction
            rectified_image, bounding_rect, grid_mask, corners, h_mask, v_mask, full_grid_mask = self._detect_table(image)
            # Store masks for later debug use
            self._current_h_mask = h_mask
            self._current_v_mask = v_mask
            self._current_grid_mask = full_grid_mask
            
            # Step 2.2: Validate table dimensions
            is_valid, message = self._validate_table(rectified_image, grid_mask)
            
            if not is_valid:
                result.has_extraction_issues = True
                result.error_message = message
                # Still create debug image to see what was detected
                try:
                    horizontal_separators, vertical_separators = self._extract_separators_from_rectified(rectified_image)
                    self._create_debug_image(
                        rectified_image,
                        horizontal_separators,
                        vertical_separators,
                        [],
                        student_id,
                        cell_margin_trim,
                        self._current_h_mask,
                        self._current_v_mask,
                        self._current_grid_mask
                    )
                except:
                    pass  # If debug fails, just skip it
                return result
            
            # Extract separators on rectified image
            horizontal_separators, vertical_separators = self._extract_separators_from_rectified(rectified_image)
            
            # Step 2.3: Extract and grade answers
            student_answers, has_ambiguous = self._extract_student_answers(
                rectified_image,
                horizontal_separators,
                vertical_separators,
                cell_margin_trim
            )
            
            # Grade the student
            question_scores, total_score, _ = grade_student_answers(
                student_answers,
                self.correct_answers,
                self.grading_rule
            )
            
            # Store results
            result.question_scores = question_scores
            result.total_score = total_score
            result.student_answers = student_answers
            result.has_ambiguous_answers = has_ambiguous
            
            # Create debug image
            self._create_debug_image(
                rectified_image,
                horizontal_separators,
                vertical_separators,
                student_answers,
                student_id,
                cell_margin_trim,
                self._current_h_mask,
                self._current_v_mask,
                self._current_grid_mask
            )
            
        except Exception as e:
            result.has_extraction_issues = True
            result.error_message = str(e)
        
        return result
    
    def _detect_table(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect and correct table perspective.
        
        Returns:
            Tuple of (rectified_image, bounding_rect, grid_mask, corners, h_mask, v_mask, grid_mask)
        """
        # A. Preprocess image
        preprocessed = preprocess_image(image)
        
        # B. Extract line masks
        h_mask, v_mask, grid_mask = extract_line_masks(preprocessed)
        
        # C. Find table candidate
        bounding_rect, contour = find_table_bounding_box(grid_mask)
        
        # D. Perspective correction
        corners = detect_corner_points(contour, bounding_rect)
        rectified, _, _ = perspective_correction(preprocessed, corners)
        
        # Also need rectified color image for debug
        corners_color = detect_corner_points(contour, bounding_rect)
        rectified_color, _, _ = perspective_correction(image, corners_color)
        
        # Store masks for debug visualization
        self._last_h_mask = h_mask
        self._last_v_mask = v_mask
        self._last_grid_mask = grid_mask
        
        return rectified_color, bounding_rect, rectified, corners, h_mask, v_mask, grid_mask
    
    def _validate_table(self, rectified_image: np.ndarray, grid_mask: np.ndarray) -> Tuple[bool, str]:
        """
        Validate table dimensions.
        
        Returns:
            Tuple of (is_valid, message)
        """
        # A. Recompute line masks
        _, _, grid_mask_rectified = extract_line_masks(grid_mask)
        
        # B & C. Extract separators with uniform spacing
        horizontal_separators = extract_separators(
            grid_mask_rectified,
            axis='horizontal',
            num_questions=self.num_questions,
            num_answers=self.num_answers,
            table_format=self.table_format
        )
        vertical_separators = extract_separators(
            grid_mask_rectified,
            axis='vertical',
            num_questions=self.num_questions,
            num_answers=self.num_answers,
            table_format=self.table_format
        )
        
        # D. Validate dimensions
        is_valid, message = validate_table_dimensions(
            horizontal_separators,
            vertical_separators,
            self.num_questions,
            self.num_answers,
            self.table_format
        )
        
        return is_valid, message
    
    def _extract_separators_from_rectified(self, rectified_image: np.ndarray) -> Tuple[List[int], List[int]]:
        """Extract separator positions from rectified image."""
        # Preprocess the rectified image
        if len(rectified_image.shape) == 3:
            preprocessed = preprocess_image(rectified_image)
        else:
            # Already preprocessed (inverted binary)
            preprocessed = rectified_image
        
        # Extract line masks
        _, _, grid_mask = extract_line_masks(preprocessed)
        
        # Extract separators with uniform spacing
        horizontal_separators = extract_separators(
            grid_mask,
            axis='horizontal',
            num_questions=self.num_questions,
            num_answers=self.num_answers,
            table_format=self.table_format
        )
        vertical_separators = extract_separators(
            grid_mask,
            axis='vertical',
            num_questions=self.num_questions,
            num_answers=self.num_answers,
            table_format=self.table_format
        )
        
        return horizontal_separators, vertical_separators
    
    def _extract_student_answers(
        self,
        rectified_image: np.ndarray,
        horizontal_separators: List[int],
        vertical_separators: List[int],
        cell_margin_trim: float
    ) -> Tuple[List[int], bool]:
        """
        Extract student's answers from the table.
        
        Returns:
            Tuple of (student_answers, has_ambiguous)
        """
        # Preprocess rectified image for answer detection
        if len(rectified_image.shape) == 3:
            preprocessed = preprocess_image(rectified_image)
        else:
            preprocessed = rectified_image
        
        # Extract cell regions
        cell_grid = extract_cell_regions(preprocessed, horizontal_separators, vertical_separators)
        
        student_answers = []
        has_ambiguous = False
        
        # Loop over each question
        for q_idx in range(self.num_questions):
            question_cells = get_question_cells(cell_grid, q_idx, self.table_format)
            
            # Detect filled cells
            filled_indices = []
            for a_idx, cell in enumerate(question_cells):
                print(q_idx, a_idx)
                cell_trimmed = trim_cell_borders(cell, margin_percent=cell_margin_trim)
                if detect_filled_cell(cell_trimmed):
                    filled_indices.append(a_idx)
                print(' ')

            # Determine answer
            if len(filled_indices) == 0:
                # No answer
                student_answers.append(-1)
            elif len(filled_indices) == 1:
                # One answer
                student_answers.append(filled_indices[0])
            else:
                # Multiple answers - ambiguous
                student_answers.append(-2)
                has_ambiguous = True
        
        return student_answers, has_ambiguous
    
    def _create_debug_image(
        self,
        rectified_image: np.ndarray,
        horizontal_separators: List[int],
        vertical_separators: List[int],
        student_answers: List[int],
        student_id: str,
        cell_margin_trim: float,
        h_mask: np.ndarray = None,
        v_mask: np.ndarray = None,
        grid_mask: np.ndarray = None
    ):
        """Create and save debug visualization with optional line masks."""
        try:
            # Create composite debug image with masks if available
            if h_mask is not None or v_mask is not None or grid_mask is not None:
                debug_image = create_composite_debug_image(
                    rectified_image,
                    horizontal_separators,
                    vertical_separators,
                    student_answers,
                    self.table_format,
                    cell_margin_trim,
                    h_mask,
                    v_mask,
                    grid_mask
                )
            else:
                debug_image = draw_cell_grid_with_answers(
                    rectified_image,
                    horizontal_separators,
                    vertical_separators,
                    student_answers,
                    self.table_format,
                    cell_margin_trim
                )
            
            # Save debug image
            debug_path = os.path.join(self.debug_dir, f"{student_id}_debug.png")
            success = cv2.imwrite(debug_path, debug_image)
            if not success:
                print(f"Warning: Failed to save debug image to {debug_path}")
            else:
                print(f"Debug image saved: {debug_path}")
        except Exception as e:
            print(f"Warning: Could not create debug image for {student_id}: {str(e)}")
    
    def process_pdf(self, pdf_path: str) -> pd.DataFrame:
        """
        Process an entire PDF file with multiple student pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DataFrame with results for all students
        """
        from pdf2image import convert_from_path
        
        # Convert PDF to images
        print(f"Converting PDF to images: {pdf_path}")
        images = convert_from_path(pdf_path)
        
        # Process each page
        results = []
        for page_idx, image in enumerate(images):
            student_id = f"student_{page_idx + 1:03d}"
            print(f"Processing {student_id}...")
            
            # Convert PIL image to numpy array
            image_np = np.array(image)
            
            # Process page
            cell_margin_trim = 20.  # Percentage of cell size to trim from borders
            result = self.process_student_page(image_np, student_id, cell_margin_trim)
            results.append(result)
        
        # Convert results to DataFrame
        df = self._results_to_dataframe(results)
        
        return df
    
    def _results_to_dataframe(self, results: List[StudentResult]) -> pd.DataFrame:
        """Convert StudentResult objects to DataFrame."""
        data = []
        for result in results:
            row_dict = result.to_dict()
            data.append(row_dict)
        
        df = pd.DataFrame(data)
        return df
    
    def save_results(self, df: pd.DataFrame, output_filename: str = "grades.csv"):
        """Save results to CSV file."""
        output_path = os.path.join(self.output_dir, output_filename)
        df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}")
        return output_path
