"""
OMR Grading System - Implementation Summary and Testing Guide

This document summarizes the complete implementation of the OMR grading system
based on your specifications.
"""

# ==============================================================================
# PROJECT STRUCTURE
# ==============================================================================

The project is organized as follows:

src/
  ├── __init__.py                 # Package initialization
  ├── image_preprocessing.py      # Image preprocessing and line extraction
  │   ├── preprocess_image()           - Grayscale, denoise, threshold, invert
  │   ├── extract_line_masks()         - Morphological operations for lines
  │   ├── find_table_bounding_box()    - Find table contours
  │   ├── detect_corner_points()       - Detect table corners
  │   └── perspective_correction()     - Apply perspective transformation
  │
  ├── table_detection.py          # Table detection and cell extraction
  │   ├── extract_separators()         - Find separator positions from signal
  │   ├── validate_table_dimensions()  - Sanity check on dimensions
  │   ├── extract_cell_regions()       - Extract individual cells
  │   ├── get_question_cells()         - Get cells for a question
  │   └── detect_filled_cell()         - Detect ink density in cell
  │
  ├── grading.py                  # Grading logic
  │   ├── GradingRule              - Configurable grading parameters
  │   ├── StudentResult            - Result storage per student
  │   └── grade_student_answers()  - Apply grading rule
  │
  ├── debug_visualization.py      # Debug image generation
  │   ├── create_debug_overlay()       - Original image overlay
  │   └── draw_cell_grid_with_answers()- Rectified image visualization
  │
  └── omr_grader.py               # Main processing pipeline
      └── OMRGrader class:
          ├── process_pdf()            - Main entry point
          ├── process_student_page()   - Process single page
          ├── _detect_table()          - Step 2.1: Detection & correction
          ├── _validate_table()        - Step 2.2: Dimension validation
          ├── _extract_separators()    - Extract separator positions
          ├── _extract_student_answers()- Step 2.3: Answer extraction
          └── save_results()           - Export to CSV

main.py                            # Command-line entry point
example_usage.py                   # Example usage demonstrations
requirements.txt                   # Python dependencies
README.md                          # Comprehensive documentation
.gitignore                         # Git ignore patterns


# ==============================================================================
# STEP-BY-STEP IMPLEMENTATION BREAKDOWN
# ==============================================================================

STEP 1: PDF TO IMAGES
  Location: OMRGrader.process_pdf()
  - Uses pdf2image.convert_from_path() to convert PDF to PIL images
  - Converts PIL images to numpy arrays for processing

STEP 2.1: TABLE DETECTION & PERSPECTIVE CORRECTION
  Location: OMRGrader._detect_table()
  - A. Preprocess image:
      - Convert to grayscale
      - Apply bilateral denoising (preserves edges)
      - Adaptive threshold (handles uneven lighting)
      - Invert colors (ink becomes white)
  - B. Extract line masks:
      - Apply morphological opening with long kernels
      - Separate horizontal and vertical kernels
      - Combine into grid mask
  - C. Find table candidate:
      - Find external contours in grid mask
      - Extract bounding rectangle
  - D. Perspective correction:
      - Detect corner points using contour approximation
      - Apply perspective transformation
  
  Returns: Rectified image, bounding rect, grid mask, corners

STEP 2.2: TABLE DIMENSION VALIDATION
  Location: OMRGrader._validate_table()
  - A. Recompute line masks on rectified image
  - B. Sum pixels along horizontal/vertical axes
  - C. Threshold to find peaks and merge adjacent ones
  - D. Validate separator counts match expected dimensions
      - Format-aware check: different validation for columns=questions vs rows=questions
      - Expected separators = dimension + 2 (for outer edges + headers)
  
  Returns: (is_valid, message)

STEP 2.3: ANSWER EXTRACTION & GRADING
  Location: OMRGrader._extract_student_answers()
  - A. Loop over each question (column or row depending on format)
  - B. For each question, isolate the cells using separator positions
  - C. Detect filled cells using ink density threshold (default: 15%)
  - D. Grade based on answer count:
      - 0 cells filled → -1 (no answer, use no_answer_points)
      - 1 cell filled → store answer index (compare with correct)
      - 2+ cells filled → -2 (ambiguous, flag page)
  - E. Save answers for debug visualization
  
  Returns: (student_answers, has_ambiguous)

STEP 3: GRADING & CSV EXPORT
  Location: OMRGrader.process_pdf()
  - Apply GradingRule to each student's answers
  - Generate per-question scores
  - Calculate total score
  - Create pandas DataFrame
  - Export to CSV with columns:
      - student_id
      - question_X_score (for each question)
      - total_score
      - issues (OK, ambiguous_answers, extraction_issues, etc.)


# ==============================================================================
# CONFIGURATION & USAGE
# ==============================================================================

COMMAND LINE USAGE:

  Basic example:
    python main.py test.pdf \
      --correct-answers 0 1 0 2 1 3 0 1 2 0 \
      --num-answers 4

  Full example with all options:
    python main.py test.pdf \
      --correct-answers 0 1 0 2 1 3 0 1 2 0 \
      --num-answers 4 \
      --table-format columns=questions \
      --correct-points 1.0 \
      --incorrect-points -0.25 \
      --no-answer-points 0.0 \
      --output-dir ./results \
      --output-file final_grades.csv

PYTHON API USAGE:

  from src.omr_grader import OMRGrader
  from src.grading import GradingRule
  
  grading_rule = GradingRule(
      correct_points=1.0,
      incorrect_points=-0.25,
      no_answer_points=0.0
  )
  
  grader = OMRGrader(
      correct_answers=[0, 1, 0, 2, 1],
      num_questions=5,
      num_answers=4,
      table_format='columns=questions',
      grading_rule=grading_rule,
      output_dir='./outputs'
  )
  
  df = grader.process_pdf('test.pdf')
  grader.save_results(df)


# ==============================================================================
# TESTING & VALIDATION
# ==============================================================================

To test the implementation:

1. Create a sample PDF with answer sheets
   - Each page: student answer sheet
   - Table with clear borders, headers, and cells
   - Students mark cells with pen/pencil

2. Run the grader:
   python main.py sample.pdf \
     --correct-answers 0 1 0 2 1 \
     --num-answers 4 \
     --table-format columns=questions

3. Check outputs:
   - ./outputs/grades.csv - Results
   - ./outputs/debug_images/student_001_debug.png - Debug images

4. Verify debug images:
   - Green rectangles = detected answers
   - Red rectangles = ambiguous answers
   - Gray grid = detected separators

5. Review CSV:
   - Check total_score column
   - Look for issues flag
   - Verify per-question scores match expected grading rule


# ==============================================================================
# KEY DESIGN DECISIONS
# ==============================================================================

1. MORPHOLOGICAL OPERATIONS:
   - Used cv2.MORPH_OPEN for line extraction (removes noise)
   - Kernel size scales with image dimensions for robustness

2. ADAPTIVE THRESHOLD:
   - Handles uneven illumination in scanned documents
   - Block size = 11 (balance between local and global)
   - C = 2 (constant subtracted from mean)

3. PERSPECTIVE CORRECTION:
   - Detects corners via contour approximation
   - Falls back to bounding rectangle if approximation fails
   - Preserves image quality better than simple rotation

4. SEPARATOR DETECTION:
   - Sum pixels along axes creates 1D signals
   - Threshold-based peak detection
   - Adjacent peak merging uses centroid calculation

5. INK DENSITY THRESHOLD:
   - Default: 15% of cell area must be white (inked)
   - Configurable via detect_filled_cell() parameter
   - Handles varying marking intensities

6. RESULT STORAGE:
   - StudentResult class encapsulates per-student data
   - to_dict() for easy DataFrame conversion
   - Issues field supports multiple flag types

7. DEBUG VISUALIZATION:
   - Separate debug images per student
   - Green for correct answers, red for ambiguous
   - Helps verify extraction accuracy before trusting grades


# ==============================================================================
# ERROR HANDLING
# ==============================================================================

The system handles various error conditions:

1. PDF_PROCESSING:
   - If PDF path invalid → File not found error
   - If PDF empty → No images returned

2. TABLE_DETECTION:
   - If no contours found → ValueError raised, page flagged
   - If perspective correction fails → handled gracefully

3. DIMENSION_VALIDATION:
   - If separator count mismatches → Page flagged with error_message
   - Validation is format-aware (columns vs rows)

4. ANSWER_EXTRACTION:
   - If cells cannot be isolated → handled (empty cell list)
   - Multiple answers detected → Page flagged as ambiguous

5. RESULT_EXPORT:
   - If output directory doesn't exist → Created automatically
   - If output file exists → Overwritten


# ==============================================================================
# PERFORMANCE CONSIDERATIONS
# ==============================================================================

- Image processing operations are O(n) where n = image pixels
- Separator detection is O(m) where m = image dimension
- Cell extraction is O(q*p) where q = questions, p = answers
- Bottleneck: PDF to image conversion (pdf2image)
- Memory: Stores all images in memory (consider streaming for large PDFs)

For typical test sheets (10 questions, 4 answers, 50 students):
- Expected processing time: 30-60 seconds
- Memory usage: ~500MB-1GB


# ==============================================================================
# FUTURE ENHANCEMENTS
# ==============================================================================

Potential improvements:

1. Handle multiple marks per question (weighted scoring)
2. Auto-detect table format instead of requiring input
3. Support for different cell marking styles (circles, checkmarks)
4. OCR for student ID extraction
5. Batch processing with progress bar
6. Streaming PDF processing for large files
7. Web interface for easy batch submission
8. Email delivery of results
9. Statistical analysis and reporting
10. Machine learning for improved mark detection


# ==============================================================================
# TROUBLESHOOTING GUIDE
# ==============================================================================

Issue: "No contours found in grid mask"
  → Check image contrast
  → Verify table has clear borders
  → Try different preprocessing parameters

Issue: "Separator mismatch"
  → Verify --num-answers matches actual table
  → Check --correct-answers count
  → Review debug images for detection issues

Issue: "Ambiguous answers" flagged
  → Review debug image for that student
  → Adjust ink_threshold parameter if too sensitive
  → Check for poor image quality

Issue: Wrong grades
  → Verify correct answers are 0-indexed
  → Check grading rule parameters
  → Review per-question scores in CSV


# ==============================================================================
"""

print(__doc__)
