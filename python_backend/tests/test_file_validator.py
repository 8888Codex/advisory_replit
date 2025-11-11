"""
Tests for file upload validation
"""
import pytest
import io
from PIL import Image
from file_validator import (
    validate_image_file,
    sanitize_filename,
    check_magic_bytes,
    FileValidationError,
)


def create_test_image(format="PNG", size=(100, 100)):
    """Helper to create a test image"""
    img = Image.new("RGB", size, color="red")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_check_magic_bytes_png():
    """Test magic byte detection for PNG"""
    png_bytes = create_test_image("PNG")
    is_valid, format_name = check_magic_bytes(png_bytes)
    assert is_valid is True
    assert format_name == "PNG"


def test_check_magic_bytes_jpeg():
    """Test magic byte detection for JPEG"""
    jpeg_bytes = create_test_image("JPEG")
    is_valid, format_name = check_magic_bytes(jpeg_bytes)
    assert is_valid is True
    assert format_name == "JPEG"


def test_check_magic_bytes_invalid():
    """Test that invalid magic bytes are rejected"""
    fake_bytes = b"This is not an image"
    is_valid, format_name = check_magic_bytes(fake_bytes)
    assert is_valid is False
    assert format_name is None


def test_validate_image_file_success():
    """Test successful image validation"""
    png_bytes = create_test_image("PNG", (200, 200))
    image, format_name = validate_image_file(png_bytes, "test.png")
    
    assert image is not None
    assert format_name in ["PNG", "JPEG", "WebP"]
    assert image.size == (200, 200)


def test_validate_image_file_too_large():
    """Test rejection of files that are too large"""
    # Create a large file (6MB of random data)
    large_bytes = b"x" * (6 * 1024 * 1024)
    
    with pytest.raises(FileValidationError, match="muito grande"):
        validate_image_file(large_bytes, "large.png", max_size_mb=5)


def test_validate_image_file_too_small():
    """Test rejection of files that are suspiciously small"""
    tiny_bytes = b"x" * 50
    
    with pytest.raises(FileValidationError):
        validate_image_file(tiny_bytes, "tiny.png")


def test_validate_image_file_dimensions_too_large():
    """Test rejection of images with dimensions too large"""
    large_image = create_test_image("PNG", (3000, 3000))
    
    with pytest.raises(FileValidationError, match="Dimensões muito grandes"):
        validate_image_file(large_image, "large.png", max_dimension=2048)


def test_validate_image_file_dimensions_too_small():
    """Test rejection of images with dimensions too small"""
    small_image = create_test_image("PNG", (30, 30))
    
    with pytest.raises(FileValidationError, match="muito pequenas"):
        validate_image_file(small_image, "small.png")


def test_validate_image_file_corrupted():
    """Test rejection of corrupted image data"""
    # Create corrupted PNG (valid magic bytes but invalid data)
    corrupted = b"\x89PNG\r\n\x1a\n" + b"corrupted data here"
    
    # Should fail with either "muito pequeno" or "corrompido"
    with pytest.raises(FileValidationError):
        validate_image_file(corrupted, "corrupted.png")


def test_validate_image_file_executable_embedded():
    """Test rejection of images with embedded executable"""
    png_bytes = create_test_image("PNG", (100, 100))
    
    # Append Windows executable signature
    malicious = png_bytes + b"MZ" + b"fake executable code"
    
    with pytest.raises(FileValidationError, match="suspeito"):
        validate_image_file(malicious, "malicious.png")


def test_sanitize_filename_basic():
    """Test basic filename sanitization"""
    result = sanitize_filename("test.png")
    assert result == "test_png"  # Dots are removed except in extension handling


def test_sanitize_filename_directory_traversal():
    """Test prevention of directory traversal"""
    result = sanitize_filename("../../../etc/passwd")
    assert ".." not in result
    assert "/" not in result
    assert "\\" not in result


def test_sanitize_filename_dangerous_chars():
    """Test removal of dangerous characters"""
    result = sanitize_filename('test:file*name?.png')
    assert ":" not in result
    assert "*" not in result
    assert "?" not in result


def test_sanitize_filename_empty():
    """Test handling of empty filename"""
    result = sanitize_filename("")
    assert result == "uploaded_file"


def test_sanitize_filename_too_long():
    """Test truncation of very long filenames"""
    long_name = "a" * 300 + ".png"
    result = sanitize_filename(long_name)
    assert len(result) <= 255

