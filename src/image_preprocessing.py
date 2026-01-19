"""Image preprocessing utilities for OMR grading."""

import cv2
import numpy as np


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for table detection.
    
    Steps:
    1. Convert to grayscale
    2. Apply light denoising (bilateral filter)
    3. Adaptive threshold
    4. Invert colors (ink becomes white, background black)
    
    Args:
        image: Input BGR image
        
    Returns:
        Preprocessed binary image (inverted)
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter for denoising (preserves edges better than median)
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply adaptive threshold to handle uneven illumination
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )
    
    # Invert colors: ink becomes white, background becomes black
    inverted = cv2.bitwise_not(binary)
    
    return inverted


def extract_line_masks(image: np.ndarray, kernel_scale: float = 0.02) -> tuple:
    """
    Extract horizontal and vertical line masks using morphological operations.
    
    Args:
        image: Preprocessed binary image
        kernel_scale: Scale factor for kernel size relative to image dimensions
        
    Returns:
        Tuple of (horizontal_mask, vertical_mask, combined_grid_mask)
    """
    height, width = image.shape

    # Calculate kernel sizes based on image dimensions
    horizontal_kernel_size = max(int(width * kernel_scale), 3)
    vertical_kernel_size = max(int(height * kernel_scale), 3)

    # Ensure odd kernel sizes
    horizontal_kernel_size = horizontal_kernel_size if horizontal_kernel_size % 2 == 1 else horizontal_kernel_size + 1
    vertical_kernel_size = vertical_kernel_size if vertical_kernel_size % 2 == 1 else vertical_kernel_size + 1

    # Create kernels for morphological operations
    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (horizontal_kernel_size, 1)
    )
    vertical_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, vertical_kernel_size)
    )

    # Extract horizontal lines (opening operation keeps long horizontal strokes)
    horizontal_mask = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)

    # Extract vertical lines (opening operation keeps long vertical strokes)
    vertical_mask = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)

    # Combine masks
    grid_mask = cv2.bitwise_or(horizontal_mask, vertical_mask)

    return horizontal_mask, vertical_mask, grid_mask


def find_table_bounding_box(grid_mask: np.ndarray) -> tuple:
    """
    Find the external contour and bounding rectangle of the table.
    
    Args:
        grid_mask: Grid mask from line extraction
        
    Returns:
        Tuple of (bounding_rect, contours) where bounding_rect is (x, y, w, h)
    """
    # Find contours in the grid mask
    contours, _ = cv2.findContours(grid_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        raise ValueError("No contours found in grid mask")
    
    # Find the largest contour (should be the table)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    return (x, y, w, h), largest_contour


def detect_corner_points(contour: np.ndarray, bounding_rect: tuple) -> np.ndarray:
    """
    Detect the corner points of the table for perspective correction.
    
    Uses contour approximation to find corners.
    
    Args:
        contour: The table contour
        bounding_rect: Bounding rectangle (x, y, w, h)
        
    Returns:
        Array of 4 corner points
    """
    # Approximate contour shape
    epsilon = 0.02 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    # If we don't get exactly 4 points, use bounding rectangle corners
    if len(approx) != 4:
        x, y, w, h = bounding_rect
        corners = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h]
        ], dtype=np.float32)
    else:
        # Extract corner points and sort them
        corners = approx.reshape(4, 2).astype(np.float32)
    
    # Sort corners: top-left, top-right, bottom-right, bottom-left
    rect = order_corners(corners)
    
    return rect


def order_corners(corners: np.ndarray) -> np.ndarray:
    """
    Order corners in standard format: top-left, top-right, bottom-right, bottom-left.
    
    Args:
        corners: Array of 4 corner points
        
    Returns:
        Ordered corners array
    """
    # Robust corner ordering using sums and differences
    # Sum (x+y) -> top-left has smallest sum, bottom-right has largest sum
    # Diff (x-y) -> top-right has smallest diff, bottom-left has largest diff
    pts = corners.reshape((4, 2))

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(4)

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]

    ordered = np.array([tl, tr, br, bl], dtype=np.float32)

    return ordered


def perspective_correction(image: np.ndarray, corners: np.ndarray) -> tuple:
    """
    Apply perspective correction to the table region.
    
    Args:
        image: Input image
        corners: 4 corner points of the table
        
    Returns:
        Tuple of (corrected_image, width, height)
    """
    # Calculate the width and height of the corrected image
    width = int(max(
        np.linalg.norm(corners[0] - corners[1]),
        np.linalg.norm(corners[2] - corners[3])
    ))
    height = int(max(
        np.linalg.norm(corners[0] - corners[3]),
        np.linalg.norm(corners[1] - corners[2])
    ))
    
    # Define destination corners (top-left, top-right, bottom-right, bottom-left)
    dst_corners = np.array([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ], dtype=np.float32)
    
    # Get perspective transformation matrix
    matrix = cv2.getPerspectiveTransform(corners, dst_corners)
    
    # Apply perspective transformation
    corrected = cv2.warpPerspective(image, matrix, (width, height))
    
    return corrected, width, height
