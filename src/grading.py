"""Grading logic for OMR answer sheets."""

from typing import List, Tuple, Dict
import numpy as np


class GradingRule:
    """Defines how to grade answers."""
    
    def __init__(self, correct_points: float = 1.0, incorrect_points: float = -0.25, no_answer_points: float = 0.0):
        """
        Initialize grading rule.
        
        Args:
            correct_points: Points for correct answer
            incorrect_points: Points for incorrect answer (can be negative)
            no_answer_points: Points for no answer
        """
        self.correct_points = correct_points
        self.incorrect_points = incorrect_points
        self.no_answer_points = no_answer_points
    
    def grade_question(self, answer_index: int, correct_index: int) -> float:
        """
        Grade a single question.
        
        Args:
            answer_index: Index of student's answer (-1 if no answer)
            correct_index: Index of correct answer
            
        Returns:
            Points earned for this question
        """
        if answer_index == -1:
            # No answer
            return self.no_answer_points
        elif answer_index == correct_index:
            # Correct answer
            return self.correct_points
        else:
            # Incorrect answer
            return self.incorrect_points


def grade_student_answers(
    student_answers: List[int],
    correct_answers: List[int],
    grading_rule: GradingRule
) -> Tuple[List[float], float, bool]:
    """
    Grade all answers for a student.
    
    Args:
        student_answers: List of student's answer indices (-1 for no answer, -2 for ambiguous)
        correct_answers: List of correct answer indices
        grading_rule: GradingRule object
        
    Returns:
        Tuple of (question_scores, total_score, has_issues)
    """
    question_scores = []
    has_issues = False
    
    for i, (answer, correct) in enumerate(zip(student_answers, correct_answers)):
        if answer == -2:
            # Ambiguous answer (multiple selections)
            question_scores.append(0.0)
            has_issues = True
        else:
            score = grading_rule.grade_question(answer, correct)
            question_scores.append(score)
    
    total_score = sum(question_scores)
    
    return question_scores, total_score, has_issues


class StudentResult:
    """Stores result for a single student."""
    
    def __init__(self, student_id: str):
        """
        Initialize student result.
        
        Args:
            student_id: Identifier for the student (e.g., page number)
        """
        self.student_id = student_id
        self.question_scores = []
        self.total_score = 0.0
        self.has_extraction_issues = False
        self.has_ambiguous_answers = False
        self.error_message = ""
        self.student_answers = []  # For debug purposes
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary for CSV export."""
        result_dict = {
            'student_id': self.student_id,
            'total_score': self.total_score,
            'issues': self._get_issues_flag()
        }
        
        # Add per-question scores
        for i, score in enumerate(self.question_scores):
            result_dict[f'question_{i+1}_score'] = score
        
        return result_dict
    
    def _get_issues_flag(self) -> str:
        """Generate issues flag string."""
        flags = []
        if self.has_extraction_issues:
            flags.append("extraction_issues")
        if self.has_ambiguous_answers:
            flags.append("ambiguous_answers")
        if self.error_message:
            flags.append(self.error_message)
        
        return "; ".join(flags) if flags else "OK"
