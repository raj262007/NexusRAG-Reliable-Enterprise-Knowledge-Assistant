import re
import hashlib
from pathlib import Path

# Windows reserved device names
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal, reserved names, and dangerous characters.
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_document"

    # Strip any directory path components (forward or backward slashes)
    name = Path(filename).name

    # Remove null bytes and control characters
    name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", name)

    # Replace forbidden path characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name).strip()

    # Prevent hidden files / current / parent dir traversal
    name = name.lstrip(". ")

    if not name:
        return "unnamed_document"

    # Split stem and extension
    parts = name.rsplit(".", 1)
    stem = parts[0]
    ext = f".{parts[1].lower()}" if len(parts) > 1 else ""

    # Check for reserved Windows filenames
    if stem.upper() in _RESERVED_NAMES:
        stem = f"safe_{stem}"

    # Limit stem length
    if len(stem) > 100:
        stem = stem[:100]

    return f"{stem}{ext}"


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content for duplicate detection."""
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()


def compute_file_hash_from_path(file_path: Path) -> str:
    """Compute SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
