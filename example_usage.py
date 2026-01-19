"""
Example usage of the OMR Grading System.

This script demonstrates how to use the OMRGrader class programmatically.
"""

from src.omr_grader import OMRGrader
from src.grading import GradingRule


def example_basic_usage():
    """
    Basic example: Grade a simple 5-question test with 4 possible answers.
    """
    # Define the correct answers (0-based indexing: 0=A, 1=B, 2=C, 3=D)
    correct_answers = [0, 1, 0, 2, 1]  # A, B, A, C, B
    
    # Define grading rule
    grading_rule = GradingRule(
        correct_points=1.0,
        incorrect_points=-0.25,
        no_answer_points=0.0
    )
    
    # Create the grader
    grader = OMRGrader(
        correct_answers=correct_answers,
        num_questions=5,
        num_answers=4,  # A, B, C, D
        table_format='columns=questions',
        grading_rule=grading_rule,
        output_dir='./outputs',
        debug_dir='./outputs/debug_images'
    )
    
    # Process a PDF file
    df = grader.process_pdf('sample_test.pdf')
    
    # Save results
    grader.save_results(df, 'grades.csv')
    
    print("Grading complete!")
    print(df)


def example_no_penalty():
    """
    Example with no penalty for wrong answers (only rewards correct answers).
    """
    correct_answers = [0, 1, 0, 2, 1]
    
    grading_rule = GradingRule(
        correct_points=10.0,
        incorrect_points=0.0,
        no_answer_points=0.0
    )
    
    grader = OMRGrader(
        correct_answers=correct_answers,
        num_questions=5,
        num_answers=4,
        table_format='columns=questions',
        grading_rule=grading_rule,
        output_dir='./outputs'
    )
    
    df = grader.process_pdf('sample_test.pdf')
    grader.save_results(df, 'grades_no_penalty.csv')


def example_different_format():
    """
    Example with different table format (rows = questions instead of columns).
    """
    correct_answers = [0, 1, 0, 2, 1]
    
    grading_rule = GradingRule(
        correct_points=1.0,
        incorrect_points=-0.25,
        no_answer_points=0.0
    )
    
    grader = OMRGrader(
        correct_answers=correct_answers,
        num_questions=5,
        num_answers=4,
        table_format='rows=questions',  # Different format
        grading_rule=grading_rule,
        output_dir='./outputs'
    )
    
    df = grader.process_pdf('sample_test.pdf')
    grader.save_results(df, 'grades_row_format.csv')


if __name__ == "__main__":
    print("OMR Grading System - Example Usage")
    print("=" * 50)
    print()
    print("To run examples, uncomment the function calls below")
    print()
    print("Available examples:")
    print("1. example_basic_usage()     - Standard grading with penalties")
    print("2. example_no_penalty()      - No penalty for wrong answers")
    print("3. example_different_format() - Different table format")
    print()
    print("For command-line usage, run:")
    print("  python main.py <pdf_path> --correct-answers 0 1 0 2 1 --num-answers 4")
