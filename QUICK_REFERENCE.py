#!/usr/bin/env python3
"""
OMR Grading System - Quick Reference Card

This file contains a quick reference for using the OMR Grading System.
"""

# ==============================================================================
# COMMAND LINE QUICK REFERENCE
# ==============================================================================

"""

1. BASIC USAGE
==============
python main.py test.pdf --correct-answers 0 1 0 2 1 --num-answers 4

2. FULL USAGE
=============
python main.py test.pdf \
  --correct-answers 0 1 0 2 1 3 0 1 2 0 \
  --num-answers 4 \
  --table-format columns=questions \
  --correct-points 1.0 \
  --incorrect-points -0.25 \
  --no-answer-points 0.0 \
  --output-dir ./results \
  --output-file final_grades.csv

3. NO PENALTY MODE
==================
python main.py test.pdf \
  --correct-answers 0 1 0 2 1 \
  --num-answers 4 \
  --incorrect-points 0.0

4. DIFFERENT TABLE FORMAT
==========================
python main.py test.pdf \
  --correct-answers 0 1 0 2 1 \
  --num-answers 4 \
  --table-format rows=questions

5. HELP
=======
python main.py --help

"""

# ==============================================================================
# PYTHON API QUICK REFERENCE
# ==============================================================================

"""

from src.omr_grader import OMRGrader
from src.grading import GradingRule

# 1. BASIC USAGE
================
grading_rule = GradingRule()  # Uses defaults
grader = OMRGrader(
    correct_answers=[0, 1, 0, 2, 1],
    num_questions=5,
    num_answers=4,
    table_format='columns=questions',
    grading_rule=grading_rule
)
df = grader.process_pdf('test.pdf')
grader.save_results(df)

# 2. CUSTOM GRADING RULE
=======================
grading_rule = GradingRule(
    correct_points=10.0,
    incorrect_points=0.0,
    no_answer_points=0.0
)
grader = OMRGrader(
    correct_answers=[0, 1, 0, 2, 1],
    num_questions=5,
    num_answers=4,
    table_format='columns=questions',
    grading_rule=grading_rule
)
df = grader.process_pdf('test.pdf')
grader.save_results(df, 'scores.csv')

# 3. DIFFERENT TABLE FORMAT
===========================
grader = OMRGrader(
    correct_answers=[0, 1, 0, 2, 1],
    num_questions=5,
    num_answers=4,
    table_format='rows=questions',  # Different format
    grading_rule=GradingRule(),
    output_dir='./my_results'
)
df = grader.process_pdf('test.pdf')
grader.save_results(df)

"""

# ==============================================================================
# OUTPUT FORMAT REFERENCE
# ==============================================================================

"""

CSV Output (grades.csv):
========================

student_id,question_1_score,question_2_score,question_3_score,total_score,issues
student_001,1.0,-0.25,1.0,1.75,OK
student_002,1.0,1.0,1.0,3.0,OK
student_003,-0.25,1.0,0.0,0.75,ambiguous_answers
student_004,1.0,1.0,1.0,3.0,extraction_issues

Issues Flag Values:
  - OK                          = No issues
  - ambiguous_answers           = Multiple marks for a question
  - extraction_issues           = Table detection problems
  - extraction_issues; ambiguous_answers = Multiple issues

Debug Images:
=============
outputs/debug_images/student_001_debug.png
outputs/debug_images/student_002_debug.png
...

Color Coding in Debug Images:
  - Green rectangle  = Detected single answer (correct)
  - Red rectangle    = Detected multiple answers (ambiguous)
  - Gray lines       = Detected table separators

"""

# ==============================================================================
# GRADING RULES EXAMPLES
# ==============================================================================

"""

Example 1: Standard Multiple Choice (1 point for correct)
=========================================================
grading_rule = GradingRule(
    correct_points=1.0,
    incorrect_points=-0.25,
    no_answer_points=0.0
)
# Result: -0.25 to +1.0 per question

Example 2: All or Nothing
==========================
grading_rule = GradingRule(
    correct_points=1.0,
    incorrect_points=0.0,
    no_answer_points=0.0
)
# Result: 0 to +1.0 per question (no penalty)

Example 3: Scaled to 100 Points (10 questions)
==============================================
grading_rule = GradingRule(
    correct_points=10.0,
    incorrect_points=0.0,
    no_answer_points=0.0
)
# Result: 0 to 100 total

Example 4: With Guessing Penalty
================================
grading_rule = GradingRule(
    correct_points=1.0,
    incorrect_points=-0.33,  # penalty for 4 choices: -1/3
    no_answer_points=0.0
)
# Result: -0.33 to +1.0 per question

"""

# ==============================================================================
# TABLE FORMAT REFERENCE
# ==============================================================================

"""

Format 1: Columns = Questions, Rows = Answers (DEFAULT)
=======================================================

        Q1   Q2   Q3   Q4
    A  [ ]  [ ]  [ ]  [ ]
    B  [ ]  [ ]  [ ]  [ ]
    C  [ ]  [ ]  [ ]  [ ]
    D  [ ]  [ ]  [ ]  [ ]

Usage: --table-format columns=questions (or omit for default)

Format 2: Rows = Questions, Columns = Answers
=============================================

        A    B    C    D
    Q1  [ ]  [ ]  [ ]  [ ]
    Q2  [ ]  [ ]  [ ]  [ ]
    Q3  [ ]  [ ]  [ ]  [ ]
    Q4  [ ]  [ ]  [ ]  [ ]

Usage: --table-format rows=questions

"""

# ==============================================================================
# TROUBLESHOOTING QUICK GUIDE
# ==============================================================================

"""

Issue: "No contours found in grid mask"
Solution:
  1. Check PDF image quality (sufficient contrast)
  2. Verify table has clear borders
  3. Try with a different page to confirm

Issue: "Separator mismatch" or "Dimensions mismatch"
Solution:
  1. Verify --num-answers matches your actual table
  2. Count correct answers and ensure list length matches
  3. Check --table-format matches your table layout
  4. Review debug images to see what was detected

Issue: "Ambiguous answers" flag appearing
Solution:
  1. Check that students only marked ONE answer per question
  2. Review debug image (red rectangles show multiple marks)
  3. Adjust ink threshold if too sensitive (in code)

Issue: Grades seem wrong
Solution:
  1. Verify --correct-answers are 0-indexed (0, 1, 2, 3 for A, B, C, D)
  2. Check grading rule parameters
  3. Review per-question scores in CSV
  4. Compare with debug images

Issue: Processing is slow
Solution:
  1. Large PDFs take time (expected)
  2. Consider processing in batches
  3. Check disk space for debug images
  4. Monitor system resources

"""

# ==============================================================================
# SETUP & INSTALLATION
# ==============================================================================

"""

One-Time Setup:
===============
bash ./setup.sh

This will:
  1. Check Python version (3.8+)
  2. Create virtual environment
  3. Install dependencies

Manual Setup:
=============
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

System Requirements (macOS):
=============================
brew install poppler  # For PDF to image conversion
python3.8+

"""

# ==============================================================================
# COMMON CONFIGURATIONS
# ==============================================================================

"""

Configuration 1: 20-Question Test, 4 Answers
============================================
python main.py test.pdf \
  --correct-answers 0 1 0 2 1 3 0 1 2 0 1 0 3 1 2 0 1 3 0 2 \
  --num-answers 4

Configuration 2: 50-Question Test, 5 Answers (SAT-Style)
========================================================
python main.py test.pdf \
  --correct-answers [50 values 0-4] \
  --num-answers 5 \
  --correct-points 1.0 \
  --incorrect-points -0.25

Configuration 3: 10-Question True/False
========================================
python main.py test.pdf \
  --correct-answers 0 1 1 0 1 0 0 1 1 0 \
  --num-answers 2 \
  --correct-points 1.0 \
  --incorrect-points 0.0

Configuration 4: Bonus Points for Correct Answers
==================================================
python main.py test.pdf \
  --correct-answers 0 1 0 2 1 \
  --num-answers 4 \
  --correct-points 5.0 \
  --incorrect-points 0.0

"""

# ==============================================================================
# FILES LOCATION REFERENCE
# ==============================================================================

"""

Project Root: /Users/ielm/Work/Codes/OMR_grading/

Key Files:
  main.py                  - Run this for CLI
  example_usage.py         - View example code
  src/omr_grader.py        - Main class (OMRGrader)
  requirements.txt         - Install dependencies
  setup.sh                 - Run for setup

Output Locations:
  outputs/grades.csv                    - Main results
  outputs/debug_images/student_001.png  - Debug images

"""

# ==============================================================================

if __name__ == "__main__":
    print(__doc__)
    print("Quick Reference Card loaded successfully!")
