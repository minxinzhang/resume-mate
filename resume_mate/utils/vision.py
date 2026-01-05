import base64
import pathlib
import pymupdf

def pdf_to_base64_images(path: pathlib.Path, zoom: float = 2.0) -> list[str]:
    """
    Converts a PDF file to a list of base64-encoded image strings (JPEG).
    
    Args:
        path: Path to the PDF file.
        zoom: Zoom factor for rendering (2.0 = 144 DPI, good for OCR/Vision).
    
    Returns:
        List of data URIs (e.g., "data:image/jpeg;base64,...").
    """
    doc = pymupdf.open(path)
    images = []
    
    # Transformation matrix for higher resolution
    mat = pymupdf.Matrix(zoom, zoom)
    
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("jpeg", jpg_quality=95)
        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        images.append(f"data:image/jpeg;base64,{base64_str}")
        
    doc.close()
    return images
