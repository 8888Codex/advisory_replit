"""
File Upload Validator
Security-focused validation for uploaded files with magic byte checking.
"""
import io
from typing import Tuple, Optional
from PIL import Image
from logger import logger

# Magic bytes for allowed image formats
ALLOWED_MAGIC_BYTES = {
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
    "WebP": b"RIFF",  # WebP starts with RIFF
}

# Maximum file size in MB (configurable via env)
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Maximum image dimensions
MAX_IMAGE_DIMENSION = 2048


class FileValidationError(Exception):
    """Raised when file validation fails"""
    pass


def check_magic_bytes(file_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Check if file starts with allowed magic bytes.
    Does NOT trust MIME type - verifies actual file content.
    
    Args:
        file_content: Raw bytes of the file
    
    Returns:
        Tuple of (is_valid, format_name)
    """
    if len(file_content) < 12:
        return False, None
    
    # Check PNG
    if file_content[:8] == ALLOWED_MAGIC_BYTES["PNG"]:
        return True, "PNG"
    
    # Check JPEG (can have different markers)
    if file_content[:3] == ALLOWED_MAGIC_BYTES["JPEG"]:
        return True, "JPEG"
    
    # Check WebP (more complex - RIFF + WEBP)
    if file_content[:4] == ALLOWED_MAGIC_BYTES["WebP"]:
        # WebP has "WEBP" at bytes 8-12
        if len(file_content) >= 12 and file_content[8:12] == b"WEBP":
            return True, "WebP"
    
    return False, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]
    
    # Remove dangerous characters
    dangerous_chars = [".", "..", "/", "\\", ":", "*", "?", '"', "<", ">", "|", "\x00"]
    for char in dangerous_chars:
        filename = filename.replace(char, "_")
    
    # Limit length
    if len(filename) > 255:
        # Keep extension
        parts = filename.rsplit(".", 1)
        if len(parts) == 2:
            name, ext = parts
            filename = name[:250] + "." + ext
        else:
            filename = filename[:255]
    
    # Ensure it's not empty
    if not filename or filename.strip() == "":
        filename = "uploaded_file"
    
    return filename


def validate_image_file(
    file_content: bytes,
    original_filename: str,
    max_size_mb: int = MAX_FILE_SIZE_MB,
    max_dimension: int = MAX_IMAGE_DIMENSION,
) -> Tuple[Image.Image, str]:
    """
    Comprehensive validation of uploaded image file.
    
    Checks:
    1. File size
    2. Magic bytes (actual format, not MIME type)
    3. PIL can open it (not corrupted)
    4. Dimensions within limits
    5. Not a disguised executable
    
    Args:
        file_content: Raw bytes of uploaded file
        original_filename: Original filename from upload
        max_size_mb: Maximum file size in MB
        max_dimension: Maximum width/height in pixels
    
    Returns:
        Tuple of (PIL Image object, format name)
    
    Raises:
        FileValidationError: If validation fails
    """
    # 1. Check file size
    file_size = len(file_content)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise FileValidationError(
            f"Arquivo muito grande. Máximo: {max_size_mb}MB, "
            f"recebido: {file_size / 1024 / 1024:.2f}MB"
        )
    
    if file_size < 100:  # Minimum viable image size
        raise FileValidationError("Arquivo muito pequeno para ser uma imagem válida")
    
    # 2. Check magic bytes
    is_valid, detected_format = check_magic_bytes(file_content)
    if not is_valid:
        logger.warning(
            "Invalid magic bytes detected",
            filename=original_filename,
            first_bytes=file_content[:12].hex(),
        )
        raise FileValidationError(
            "Formato de arquivo não permitido. Use PNG, JPEG ou WebP."
        )
    
    logger.debug("Magic bytes valid", format=detected_format)
    
    # 3. Try to open with PIL (validates it's a real image)
    try:
        image = Image.open(io.BytesIO(file_content))
        image.load()  # Force loading to detect corruption
    except Exception as e:
        logger.warning(
            "PIL failed to open image",
            filename=original_filename,
            error=str(e),
        )
        raise FileValidationError(
            f"Arquivo corrompido ou não é uma imagem válida: {str(e)}"
        )
    
    # 4. Check dimensions
    width, height = image.size
    if width > max_dimension or height > max_dimension:
        logger.warning(
            "Image dimensions too large",
            filename=original_filename,
            width=width,
            height=height,
            max=max_dimension,
        )
        raise FileValidationError(
            f"Dimensões muito grandes. Máximo: {max_dimension}x{max_dimension}px, "
            f"recebido: {width}x{height}px"
        )
    
    if width < 50 or height < 50:
        raise FileValidationError(
            "Dimensões muito pequenas. Mínimo: 50x50px"
        )
    
    # 5. Verify PIL format matches magic bytes
    pil_format = image.format
    if pil_format not in ["PNG", "JPEG", "WebP"]:
        logger.warning(
            "PIL detected unexpected format",
            filename=original_filename,
            pil_format=pil_format,
            magic_format=detected_format,
        )
        raise FileValidationError(
            f"Formato inesperado: {pil_format}. Use PNG, JPEG ou WebP."
        )
    
    # 6. Additional security: check for executable signatures hidden in image
    # (Common attack: append executable to valid image)
    exe_signatures = [
        b"MZ",  # Windows executable
        b"\x7fELF",  # Linux executable
        b"#!/",  # Script shebang
    ]
    
    for signature in exe_signatures:
        if signature in file_content:
            logger.error(
                "Executable signature found in image",
                filename=original_filename,
                signature=signature.hex(),
            )
            raise FileValidationError(
                "Arquivo contém conteúdo suspeito e foi rejeitado"
            )
    
    logger.info(
        "Image validation passed",
        filename=original_filename,
        format=pil_format,
        width=width,
        height=height,
        size_kb=file_size / 1024,
    )
    
    return image, pil_format


def optimize_image(
    image: Image.Image,
    max_dimension: int = MAX_IMAGE_DIMENSION,
    quality: int = 85,
) -> bytes:
    """
    Optimize image for storage.
    - Resize if too large
    - Convert to RGB if necessary
    - Compress
    
    Args:
        image: PIL Image object
        max_dimension: Maximum width/height
        quality: JPEG quality (1-100)
    
    Returns:
        Optimized image as bytes
    """
    # Resize if needed
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        logger.debug("Image resized", new_size=image.size)
    
    # Convert RGBA to RGB (for JPEG compatibility)
    if image.mode == "RGBA":
        # Create white background
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])  # Use alpha as mask
        image = rgb_image
        logger.debug("Converted RGBA to RGB")
    elif image.mode not in ["RGB", "L"]:
        image = image.convert("RGB")
        logger.debug("Converted to RGB", original_mode=image.mode)
    
    # Save to bytes with optimization
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    optimized_bytes = output.getvalue()
    
    logger.debug(
        "Image optimized",
        original_format=image.format,
        optimized_size_kb=len(optimized_bytes) / 1024,
    )
    
    return optimized_bytes


__all__ = [
    "validate_image_file",
    "sanitize_filename",
    "optimize_image",
    "FileValidationError",
]

