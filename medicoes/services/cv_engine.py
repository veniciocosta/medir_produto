import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from django.conf import settings

def reorder_points(points: np.ndarray) -> np.ndarray:
    """
    Robustly reorders a 4-point convex polygon contour into standard order:
    [Top-Left, Top-Right, Bottom-Left, Bottom-Right]
    
    Uses standard horizontal and vertical sorting boundaries to ensure
    robustness against paper rotations in the frame.
    """
    points = points.reshape((4, 2))
    new_points = np.zeros((4, 2), dtype=np.float32)
    
    # Sort points by their x-coordinates
    xsort = points[np.argsort(points[:, 0])]
    
    left_pts = xsort[:2]
    right_pts = xsort[2:]
    
    # Sort left points by y-coordinates
    # Smaller y is Top-Left, larger y is Bottom-Left
    left_pts_ysort = left_pts[np.argsort(left_pts[:, 1])]
    new_points[0] = left_pts_ysort[0]  # Top-Left
    new_points[2] = left_pts_ysort[1]  # Bottom-Left
    
    # Sort right points by y-coordinates
    # Smaller y is Top-Right, larger y is Bottom-Right
    right_pts_ysort = right_pts[np.argsort(right_pts[:, 1])]
    new_points[1] = right_pts_ysort[0]  # Top-Right
    new_points[3] = right_pts_ysort[1]  # Bottom-Right
    
    return new_points


def get_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates the Euclidean distance between two 2D points."""
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5


def get_label_pos(ptA: Tuple[int, int], ptB: Tuple[int, int], offset_px: int = 15) -> Tuple[int, int]:
    """
    Calculates a centered text position offset perpendicularly from the vector AB.
    Prevents text from overlapping measurement arrows and box lines.
    """
    mid_x = int((ptA[0] + ptB[0]) / 2)
    mid_y = int((ptA[1] + ptB[1]) / 2)
    
    dx = ptB[0] - ptA[0]
    dy = ptB[1] - ptA[1]
    dist = (dx**2 + dy**2)**0.5
    if dist == 0:
        return (mid_x, mid_y)
    
    # Perpendicular unit vector (-dy, dx)
    perp_x = -dy / dist
    perp_y = dx / dist
    
    # Shift coordinate by the perpendicular offset
    label_x = int(mid_x + perp_x * offset_px)
    label_y = int(mid_y + perp_y * offset_px)
    
    return (label_x, label_y)


def analyze_product_image(
    image_bytes: bytes,
    scale: int = 3,
    min_a4_area: int = 50000,
    min_product_area: int = 2000,
    config: Any = None,
    width_offset_mm_override: Optional[float] = None,
    length_offset_mm_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    Analyzes an inspection photo to measure products placed on a white A4 reference paper.
    Enforces Portrait/Landscape Isotropic Perspective Warping to guarantee rotation-invariance.
    Employs dual Grayscale + Saturation (HSV) Canny edge detection for high sensitivity.
    Compensates for blooming swelling by applying CONTOUR_EROSION_FACTOR pixel erosion.
    
    Args:
        image_bytes: Raw bytes of the uploaded image.
        scale: Pixel-to-mm scaling factor for warping (default 3 pixels/mm = 30 pixels/cm).
        min_a4_area: Minimum contour area to qualify as the A4 sheet.
        min_product_area: Minimum contour area inside the A4 sheet to qualify as a product.
        config: SKUConfiguration object or dict containing per-SKU custom metrology and CV parameters.
        
    Returns:
        A dictionary containing success indicators, item lists, and marked images.
    """
    # 1. Decode image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        return {
            'success': False,
            'error': "Dados de imagem inválidos. Não foi possível decodificar o arquivo enviado.",
            'total_items': 0,
            'items': [],
            'annotated_image': b''
        }
    
    # Extract dynamic configuration values or fallback to standard defaults
    blur_kernel_size = 5
    canny_threshold_low = 30
    canny_threshold_high = 80
    erosion_factor = 1
    width_offset_mm = 0.00
    length_offset_mm = 0.00
    
    if config is not None:
        if hasattr(config, 'blur_kernel_size'):
            blur_kernel_size = getattr(config, 'blur_kernel_size', 5)
            canny_threshold_low = getattr(config, 'canny_threshold_low', 30)
            canny_threshold_high = getattr(config, 'canny_threshold_high', 80)
            erosion_factor = getattr(config, 'erosion_amount', 1)
            width_offset_mm = float(getattr(config, 'width_offset_mm', 0.00))
            length_offset_mm = float(getattr(config, 'length_offset_mm', 0.00))
        elif isinstance(config, dict):
            blur_kernel_size = config.get('blur_kernel_size', 5)
            canny_threshold_low = config.get('canny_threshold_low', 30)
            canny_threshold_high = config.get('canny_threshold_high', 80)
            erosion_factor = config.get('erosion_amount', 1)
            width_offset_mm = float(config.get('width_offset_mm', 0.00))
            length_offset_mm = float(config.get('length_offset_mm', 0.00))
            
    if width_offset_mm_override is not None:
        width_offset_mm = float(width_offset_mm_override)
    if length_offset_mm_override is not None:
        length_offset_mm = float(length_offset_mm_override)
    
    # 2. Process image to locate the A4 reference paper with tight edge bounds
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1)
    edges = cv2.Canny(blurred, 80, 150)
    
    # Tight morph kernel and 1 single iteration to close gaps without swelling bounds
    kernel_tight = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel_tight, iterations=1)
    eroded = cv2.erode(dilated, kernel_tight, iterations=1)
    
    # Find outer contours
    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    a4_contour = None
    max_area = 0
    
    for c in contours:
        area = cv2.contourArea(c)
        if area > min_a4_area:
            perimeter = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
            if len(approx) == 4 and area > max_area:
                a4_contour = approx
                max_area = area
 
    if a4_contour is None:
        return {
            'success': False,
            'error': (
                "Folha A4 de referência não detectada. Por favor, certifique-se de que a folha A4 branca "
                "está totalmente visível, desdobrada e possui alto contraste com o fundo."
            ),
            'total_items': 0,
            'items': [],
            'annotated_image': b''
        }
    
    # 3. Dynamic Isotropic Perspective Warp
    # Determine portrait/landscape orientation based on physical dimensions in frame
    reordered_a4 = reorder_points(a4_contour)
    
    side_top = get_distance(reordered_a4[0], reordered_a4[1])
    side_bottom = get_distance(reordered_a4[2], reordered_a4[3])
    side_left = get_distance(reordered_a4[0], reordered_a4[2])
    side_right = get_distance(reordered_a4[1], reordered_a4[3])
    
    w_est = (side_top + side_bottom) / 2
    h_est = (side_left + side_right) / 2
    
    # Standard A4 size is 210mm x 297mm
    if w_est > h_est:
        # A4 is in landscape orientation in camera view
        a4_width_cm = 29.7
        a4_height_cm = 21.0
    else:
        # A4 is in portrait orientation in camera view
        a4_width_cm = 21.0
        a4_height_cm = 29.7
        
    a4_width_px = int(a4_width_cm * 10 * scale)
    a4_height_px = int(a4_height_cm * 10 * scale)
    
    # DIAGNOSTIC LOG: Print calculated pixel area and verify precise 1:1.414 aspect ratio scaling
    warped_a4_area = a4_width_px * a4_height_px
    print(f"[DIAGNOSTIC] Warped A4 Sheet: {a4_width_px}px x {a4_height_px}px | "
          f"Area: {warped_a4_area}px | Aspect Ratio: {a4_width_px / a4_height_px:.4f} "
          f"(Target: {a4_width_cm / a4_height_cm:.4f})")
    
    src_points = np.float32(reordered_a4)
    dst_points = np.float32([
        [0, 0],
        [a4_width_px, 0],
        [0, a4_height_px],
        [a4_width_px, a4_height_px]
    ])
    
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(image, matrix, (a4_width_px, a4_height_px))
    
    # Crop borders to remove edge shadow artifacts (padding = 20 pixels)
    pad = 20
    h_warped, w_warped = warped.shape[:2]
    warped_height = h_warped - pad
    warped_width = w_warped - pad
    warped_cropped = warped[pad : warped_height, pad : warped_width]
    
    # Isotropic scale factor: 1 cm = scale * 10 pixels in BOTH dimensions
    pixels_per_cm = scale * 10.0
    
    # 4. Find products inside the cropped, warped A4 sheet
    # We use both Grayscale and Saturation channels to capture dark objects and high-brightness colored objects
    warped_gray = cv2.cvtColor(warped_cropped, cv2.COLOR_BGR2GRAY)
    # Dynamic Gaussian Blur Kernel (must be odd)
    blur_k = (blur_kernel_size, blur_kernel_size) if blur_kernel_size % 2 != 0 else (5, 5)
    warped_blur = cv2.GaussianBlur(warped_gray, blur_k, 1)
    
    # Extract Saturation channel to detect light-colored objects (e.g. yellow) against white background
    warped_hsv = cv2.cvtColor(warped_cropped, cv2.COLOR_BGR2HSV)
    warped_sat = warped_hsv[:, :, 1]
    warped_sat_blur = cv2.GaussianBlur(warped_sat, blur_k, 1)
    
    # Apply dynamic Canny thresholds, scaling proportionally for the saturation channel
    canny_low_sat = max(5, int(canny_threshold_low * 2 / 3))
    canny_high_sat = max(10, int(canny_threshold_high * 3 / 4))
    
    edges_gray = cv2.Canny(warped_blur, canny_threshold_low, canny_threshold_high)
    edges_sat = cv2.Canny(warped_sat_blur, canny_low_sat, canny_high_sat)
    
    # Combine edges using bitwise OR (captures both dark and light/colored objects)
    warped_edges = cv2.bitwise_or(edges_gray, edges_sat)
    
    kernel_contour = np.ones((5, 5), np.uint8)
    warped_dilated = cv2.dilate(warped_edges, kernel_contour, iterations=2)
    warped_eroded = cv2.erode(warped_dilated, kernel_contour, iterations=1)
    
    sub_contours, _ = cv2.findContours(warped_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_items = []
    annotated_output = warped_cropped.copy()
    
    # erosion_factor is dynamically defined at the beginning from the SKU configuration
    
    item_index = 1
    
    for c in sub_contours:
        area = cv2.contourArea(c)
        if area > min_product_area:
            # Apply contour erosion to compensate for threshold blooming swelling
            if erosion_factor > 0:
                # 1. Create a single-contour binary mask
                c_mask = np.zeros(warped_gray.shape, dtype=np.uint8)
                cv2.drawContours(c_mask, [c], -1, 255, -1)
                
                # 2. Erode the mask using a tight 3x3 kernel
                erosion_kernel = np.ones((3, 3), np.uint8)
                eroded_mask = cv2.erode(c_mask, erosion_kernel, iterations=erosion_factor)
                
                # 3. Retrieve the re-tightened contour
                eroded_contours, _ = cv2.findContours(eroded_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if eroded_contours:
                    # Select the largest contour resulting from erosion
                    c = max(eroded_contours, key=cv2.contourArea)
            
            # Fit rotated bounding box
            rect = cv2.minAreaRect(c)
            (cx, cy), (w, h), angle = rect
            
            # Corner coordinates of the rotated bounding box
            box = cv2.boxPoints(rect)
            box = np.intp(box)
            
            p0, p1, p2, p3 = box[0], box[1], box[2], box[3]
            
            # 5. Classify length (longer axis) and width (shorter axis) mathematically
            d01 = get_distance(p0, p1)
            d12 = get_distance(p1, p2)
            
            if d01 >= d12:
                # Vector p0 -> p1 is the long axis (Length)
                # Vector p1 -> p2 is the short axis (Width)
                length_pts = (p0, p1)
                width_pts = (p1, p2)
                length_px = d01
                width_px = d12
            else:
                # Vector p1 -> p2 is the long axis (Length)
                # Vector p0 -> p1 is the short axis (Width)
                length_pts = (p1, p2)
                width_pts = (p0, p1)
                length_px = d12
                width_px = d01
                
            # Convert metrology offsets from mm to cm
            w_offset_cm = float(width_offset_mm) / 10.0
            l_offset_cm = float(length_offset_mm) / 10.0
            
            # Apply offsets and round to 2 decimal places for sub-millimeter precision
            length_cm = round((length_px / pixels_per_cm) + l_offset_cm, 2)
            width_cm = round((width_px / pixels_per_cm) + w_offset_cm, 2)
            
            # Defensive validation to prevent zero or negative dimensions
            length_cm = max(0.01, length_cm)
            width_cm = max(0.01, width_cm)
            
            # 6. Extract Color Properties (RGB + Grayscale) using binary mask
            mask = np.zeros(warped_cropped.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, [c], -1, 255, -1)
            
            avg_gray = int(round(cv2.mean(warped_gray, mask=mask)[0]))
            avg_bgr = cv2.mean(warped_cropped, mask=mask)[:3]
            avg_rgb = [int(round(avg_bgr[2])), int(round(avg_bgr[1])), int(round(avg_bgr[0]))]
            
            detected_items.append({
                'item_index': item_index,
                'length_cm': length_cm,
                'width_cm': width_cm,
                'grayscale_value': avg_gray,
                'r_value': avg_rgb[0],
                'g_value': avg_rgb[1],
                'b_value': avg_rgb[2]
            })
            
            # 7. Draw Visual Markups (Minimal B2B clinical style)
            # Draw 1px Tech-Cyan bounding rotated box
            cv2.drawContours(annotated_output, [box], 0, (255, 255, 0), 1)
            
            # Draw subtle center circle and text for ID indicator
            cv2.circle(annotated_output, (int(cx), int(cy)), 2, (120, 200, 50), -1)
            cv2.putText(
                annotated_output, f"#{item_index}", (int(cx) + 5, int(cy) + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA
            )
            
            # Combine measurements and place elegantly above top boundary
            top_vertex = min(box, key=lambda p: p[1])
            text_x = max(5, min(annotated_output.shape[1] - 80, int(top_vertex[0])))
            text_y = max(15, int(top_vertex[1]) - 5)
            cv2.putText(
                annotated_output, f"{width_cm}x{length_cm} cm", (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA
            )
            
            item_index += 1

    # Encode annotated image to JPEG bytes
    _, img_encoded = cv2.imencode('.jpg', annotated_output)
    annotated_image_bytes = img_encoded.tobytes()
    
    return {
        'success': True,
        'error': '',
        'total_items': len(detected_items),
        'items': detected_items,
        'annotated_image': annotated_image_bytes
    }
