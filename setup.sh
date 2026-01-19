#!/bin/bash
# Quick start script for OMR Grading System setup

set -e

echo "=================================================="
echo "OMR Grading System - Quick Start Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created at ./venv"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=================================================="
echo "Setup complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Prepare your PDF file with scanned answer sheets"
echo ""
echo "2. Run the grader:"
echo "   python main.py <pdf_path> \\"
echo "     --correct-answers 0 1 0 2 1 \\"
echo "     --num-answers 4"
echo ""
echo "3. Check results:"
echo "   - Grades: ./outputs/grades.csv"
echo "   - Debug images: ./outputs/debug_images/"
echo ""
echo "For more information, see README.md or run:"
echo "   python main.py --help"
echo ""
