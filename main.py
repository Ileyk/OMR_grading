"""
OMR Grading System - Main Script

This script performs automatic grading of optical mark recognition answer sheets.
"""

import argparse
from pathlib import Path

from src.omr_grader import OMRGrader
from src.grading import GradingRule


def main():
    """Main entry point for the OMR grading system."""
    
    parser = argparse.ArgumentParser(
        description="OMR Grading System - Automatic grading based on optical mark recognition"
    )
    
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file with scanned answer sheets"
    )
    
    parser.add_argument(
        "--correct-answers",
        type=int,
        nargs="+",
        required=True,
        help="List of correct answer indices (0-based, space-separated)"
    )
    
    parser.add_argument(
        "--num-answers",
        type=int,
        required=True,
        help="Number of possible answers per question (P)"
    )
    
    parser.add_argument(
        "--table-format",
        type=str,
        choices=["columns=questions", "rows=questions"],
        default="columns=questions",
        help="Table format: columns=questions (default) or rows=questions"
    )
    
    parser.add_argument(
        "--correct-points",
        type=float,
        default=1.0,
        help="Points for correct answer (default: 1.0)"
    )
    
    parser.add_argument(
        "--incorrect-points",
        type=float,
        default=-0.25,
        help="Points for incorrect answer (default: -0.25)"
    )
    
    parser.add_argument(
        "--no-answer-points",
        type=float,
        default=0.0,
        help="Points for no answer (default: 0.0)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./outputs",
        help="Output directory for results and debug images"
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default="grades.csv",
        help="Output CSV filename"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    num_questions = len(args.correct_answers)
    
    # Create grading rule
    grading_rule = GradingRule(
        correct_points=args.correct_points,
        incorrect_points=args.incorrect_points,
        no_answer_points=args.no_answer_points
    )
    
    # Create OMR grader
    grader = OMRGrader(
        correct_answers=args.correct_answers,
        num_questions=num_questions,
        num_answers=args.num_answers,
        table_format=args.table_format,
        grading_rule=grading_rule,
        output_dir=args.output_dir,
        debug_dir=f"{args.output_dir}/debug_images"
    )
    
    # Process PDF
    print(f"Processing PDF: {pdf_path}")
    print(f"Number of questions: {num_questions}")
    print(f"Number of possible answers: {args.num_answers}")
    print(f"Table format: {args.table_format}")
    print(f"Grading rule: correct={args.correct_points}, incorrect={args.incorrect_points}, no_answer={args.no_answer_points}")
    print()
    
    try:
        df = grader.process_pdf(str(pdf_path))
        
        # Save results
        output_path = grader.save_results(df, args.output_file)
        
        print()
        print("Results Summary:")
        print(f"Total students processed: {len(df)}")
        print(f"Results saved to: {output_path}")
        print(f"Debug images saved to: {args.output_dir}/debug_images/")
        print()
        print("First few rows of results:")
        print(df.head())
        
        return 0
    
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
