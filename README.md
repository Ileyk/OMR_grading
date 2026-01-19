# OMR Grading System

Automatic grading system for optical mark recognition (OMR) answer sheets using Python and OpenCV.

## Features

- **PDF Processing**: Convert multi-page PDF documents into individual student answer sheets
- **Table Detection**: Automatically detect and isolate the answer table using morphological operations
- **Perspective Correction**: Correct for slight rotations and skew in scanned documents
- **Robust Answer Detection**: Detect filled cells using ink density thresholding
- **Comprehensive Validation**: Sanity checks on table dimensions and answer ambiguities
- **Flexible Grading**: Customizable grading rules (correct, incorrect, no-answer points)
- **Debug Visualization**: Generate debug images showing detected tables and marked answers for manual verification
- **CSV Export**: Export results with per-question scores, total grades, and issue flags

## Project Structure

```
OMR_grading/
├── src/
│   ├── __init__.py
│   ├── image_preprocessing.py    # Image preprocessing and line extraction
│   ├── table_detection.py        # Table detection and cell extraction
│   ├── grading.py                # Grading logic and result storage
│   ├── debug_visualization.py    # Debug image generation
│   └── omr_grader.py             # Main processing pipeline
├── outputs/
│   ├── debug_images/             # Debug visualizations (auto-created)
│   └── grades.csv                # Results file (auto-created)
├── main.py                        # Entry point script
├── requirements.txt               # Python dependencies
└── README.md
```

## Installation

### Prerequisites

- Python 3.8+
- System libraries for image processing (on macOS):
  ```bash
  brew install poppler  # Required for PDF to image conversion
  ```

### Setup

1. Clone the repository:
   ```bash
   cd /Users/ielm/Work/Codes/OMR_grading
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python main.py <pdf_path> \
  --correct-answers 0 1 0 2 1 \
  --num-answers 4
```

### Full Example

```bash
python main.py scanned_tests.pdf \
  --correct-answers 0 1 0 2 1 3 0 1 2 0 \
  --num-answers 4 \
  --table-format columns=questions \
  --correct-points 1.0 \
  --incorrect-points -0.25 \
  --no-answer-points 0.0 \
  --output-dir ./results \
  --output-file final_grades.csv
```

### Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `pdf_path` | Yes | - | Path to the PDF file with scanned answer sheets |
| `--correct-answers` | Yes | - | List of correct answer indices (0-based, space-separated) |
| `--num-answers` | Yes | - | Number of possible answers per question (P) |
| `--table-format` | No | `columns=questions` | Table format: `columns=questions` or `rows=questions` |
| `--correct-points` | No | `1.0` | Points awarded for correct answer |
| `--incorrect-points` | No | `-0.25` | Points awarded for incorrect answer |
| `--no-answer-points` | No | `0.0` | Points awarded for no answer |
| `--output-dir` | No | `./outputs` | Output directory for results and debug images |
| `--output-file` | No | `grades.csv` | Output CSV filename |

## Input Format

### PDF Document

- Each page contains a single student's answer sheet
- Pages should contain a table with:
  - Outer edges (borders)
  - Header row (for column labels)
  - Header column (for row labels)
  - Answer cells marked by the student

### Table Formats

The script supports two table configurations:

**Format 1: Columns = Questions, Rows = Answers**
```
        Q1   Q2   Q3
    A  [  ] [  ] [  ]
    B  [  ] [  ] [  ]
    C  [  ] [  ] [  ]
    D  [  ] [  ] [  ]
```

**Format 2: Rows = Questions, Columns = Answers**
```
        A    B    C    D
    Q1  [  ] [  ] [  ] [  ]
    Q2  [  ] [  ] [  ] [  ]
    Q3  [  ] [  ] [  ] [  ]
```

## Output Format

### CSV File

The output CSV contains one row per student with:

| Column | Description |
|--------|-------------|
| `student_id` | Student identifier (e.g., `student_001`) |
| `question_1_score` | Points earned on question 1 |
| `question_2_score` | Points earned on question 2 |
| ... | ... |
| `total_score` | Sum of all question scores |
| `issues` | Issue flag (e.g., `ambiguous_answers`, `extraction_issues`, or `OK`) |

### Example Output

```
student_id,question_1_score,question_2_score,question_3_score,total_score,issues
student_001,1.0,-0.25,1.0,1.75,OK
student_002,1.0,1.0,1.0,3.0,OK
student_003,-0.25,1.0,0.0,0.75,ambiguous_answers
student_004,1.0,1.0,1.0,3.0,extraction_issues
```

### Debug Images

For each student, a debug visualization is saved to `outputs/debug_images/student_XXX_debug.png` showing:

- Detected cell grid (gray lines)
- Student's answers highlighted in **green** (correctly detected single answer)
- Ambiguous answers highlighted in **red** (multiple marks detected)

## Processing Pipeline

### Step 1: Image Preprocessing
- Convert to grayscale
- Apply bilateral denoising
- Adaptive thresholding (handles uneven lighting)
- Invert colors (ink becomes white)

### Step 2: Line Detection
- Extract horizontal and vertical lines using morphological opening
- Combine into a grid mask

### Step 3: Table Localization
- Find external contours in grid mask
- Detect table corners using contour approximation
- Apply perspective correction for skew/rotation

### Step 4: Dimension Validation
- Extract separator positions by summing pixels along axes
- Merge adjacent peaks into separator positions
- Validate against expected table dimensions

### Step 5: Answer Extraction
- For each question, isolate the corresponding cells
- Detect filled cells using ink density threshold
- Handle three cases:
  - No answer → apply no-answer points
  - One answer → compare with correct answer
  - Multiple answers → flag as ambiguous

### Step 6: Grading & Output
- Apply grading rules to generate per-question and total scores
- Export results to CSV
- Generate debug visualizations

## Troubleshooting

### Issue: "No contours found in grid mask"

**Cause**: The image preprocessing may not be detecting the table properly.

**Solutions**:
- Ensure the PDF has sufficient contrast between table edges and background
- Check that the scanned image is not heavily skewed
- Verify the table has clear borders

### Issue: "Horizontal/Vertical separators mismatch"

**Cause**: The detected number of separators doesn't match the expected table dimensions.

**Solutions**:
- Verify the `--num-answers` value matches your table
- Check that `--correct-answers` has the correct count
- Ensure `--table-format` matches your actual table layout
- Review debug images to see what was detected

### Issue: "Ambiguous answers" flag

**Cause**: Multiple cells were detected as filled for a single question.

**Possible reasons**:
- Student marked multiple answers for one question
- Image quality issues causing false detections

**Action**: Review the debug image for that student to verify.

## Known Limitations

1. **Table Orientation**: All pages must have the same general orientation (slight rotations ±10° are handled)
2. **Cell Marking Style**: Assumes marks are darker ink/pencil on lighter background
3. **Regular Grid**: Assumes the table has regularly-spaced separators
4. **Single Mark Per Question**: Cannot distinguish between intentional and accidental multiple marks

## Dependencies

- **opencv-python**: Image processing and morphological operations
- **pdf2image**: PDF to image conversion
- **numpy**: Numerical operations
- **pandas**: Result aggregation and CSV export
- **Pillow**: Image handling

## License

This project is part of the OMR grading system.

## Support

For issues or feature requests, please open an issue in the repository.
