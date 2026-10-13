"""Convert images embedded in decks into PNG files an agent can read.

PowerPoint stores many screenshots as EMF or WMF metafiles that wrap a single
bitmap. Those bitmaps are extracted directly from the metafile records. Vector
metafiles fall back to Inkscape when it is installed.
"""
from __future__ import annotations

import io
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

MAX_WIDTH = 1600

# EMF records that carry a device-independent bitmap, mapped to the offset of
# their (offBmi, cbBmi, offBits, cbBits) fields within the record.
_EMF_DIB_RECORDS = {
    76: 84,   # EMR_BITBLT
    77: 100,  # EMR_STRETCHBLT
    80: 48,   # EMR_SETDIBITSTODEVICE
    81: 48,   # EMR_STRETCHDIBITS
}
_EMR_EOF = 14

# WMF records that carry a bitmap, mapped to the number of 16-bit parameters
# that precede the BITMAPINFO structure.
_WMF_DIB_RECORDS = {
    0x0B41: 10,  # META_DIBSTRETCHBLT (with bitmap)
    0x0F43: 11,  # META_STRETCHDIB
    0x0940: 8,   # META_DIBBITBLT (with bitmap)
}


def _bmp_from_dib(dib: bytes) -> Image.Image:
    """Wrap a packed DIB (BITMAPINFO followed by pixels) in a BMP file header."""
    header_size = struct.unpack_from("<I", dib, 0)[0]
    bit_count = struct.unpack_from("<H", dib, 14)[0]
    colors_used = struct.unpack_from("<I", dib, 32)[0] if header_size >= 36 else 0
    compression = struct.unpack_from("<I", dib, 16)[0] if header_size >= 20 else 0
    palette = (colors_used or (1 << bit_count if bit_count <= 8 else 0)) * 4
    if compression == 3 and header_size == 40:  # BI_BITFIELDS: three colour masks follow
        palette += 12
    pixels_offset = 14 + header_size + palette
    bmp = b"BM" + struct.pack("<IHHI", 14 + len(dib), 0, 0, pixels_offset) + dib
    return Image.open(io.BytesIO(bmp)).convert("RGB")


def _emf_bitmaps(data: bytes) -> list[Image.Image]:
    out, pos = [], 0
    while pos + 8 <= len(data):
        rtype, rsize = struct.unpack_from("<II", data, pos)
        if rsize < 8 or pos + rsize > len(data):
            break
        if rtype in _EMF_DIB_RECORDS:
            off_bmi, cb_bmi, off_bits, cb_bits = struct.unpack_from(
                "<IIII", data, pos + _EMF_DIB_RECORDS[rtype])
            if cb_bmi and cb_bits:
                bmi = data[pos + off_bmi:pos + off_bmi + cb_bmi]
                bits = data[pos + off_bits:pos + off_bits + cb_bits]
                header = b"BM" + struct.pack("<IHHI", 14 + cb_bmi + cb_bits, 0, 0, 14 + cb_bmi)
                out.append(Image.open(io.BytesIO(header + bmi + bits)).convert("RGB"))
        if rtype == _EMR_EOF:
            break
        pos += rsize
    return out


def _wmf_bitmaps(data: bytes) -> list[Image.Image]:
    pos = 22 if data[:4] == b"\xd7\xcd\xc6\x9a" else 0  # skip the placeable header
    pos += struct.unpack_from("<H", data, pos + 2)[0] * 2  # skip the WMF header
    out = []
    while pos + 6 <= len(data):
        size_words, func = struct.unpack_from("<IH", data, pos)
        if size_words < 3:
            break
        if func in _WMF_DIB_RECORDS:
            start = pos + 6 + _WMF_DIB_RECORDS[func] * 2
            out.append(_bmp_from_dib(data[start:pos + size_words * 2]))
        pos += size_words * 2
    return out


def _flatten(image: Image.Image) -> Image.Image:
    """RGB on a white background: transparent pixels must not turn black."""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _is_emf(data: bytes) -> bool:
    return len(data) > 44 and struct.unpack_from("<I", data, 0)[0] == 1 and data[40:44] == b" EMF"


def _is_wmf(data: bytes) -> bool:
    """A placeable WMF, or a bare WMF header (type 1 or 2, 9-word header, version 1.0 or 3.0). PowerPoint sometimes
    stores a WMF under an .emf name, so the content decides."""
    if data[:4] == b"\xd7\xcd\xc6\x9a":
        return True
    if len(data) < 18:
        return False
    mt_type, header_words, version = struct.unpack_from("<HHH", data, 0)
    return mt_type in (1, 2) and header_words == 9 and version in (0x0100, 0x0300)


def _inkscape_png(data: bytes, suffix: str) -> Image.Image | None:
    exe = shutil.which("inkscape")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp, "in" + suffix), Path(tmp, "out.png")
        src.write_bytes(data)
        subprocess.run([exe, str(src), "--export-type=png", f"--export-filename={dst}"],
                       capture_output=True, timeout=120)
        return _flatten(Image.open(dst)) if dst.exists() else None


def to_png(blob: bytes, ext: str) -> tuple[Image.Image | None, str]:
    """Return (image, source_format). The image is None when it cannot be decoded."""
    ext = ext.lower().lstrip(".")
    if _is_emf(blob):
        images, fmt = _emf_bitmaps(blob), "emf"
    elif ext == "wmf" or _is_wmf(blob):
        images, fmt = _wmf_bitmaps(blob), "wmf"
    else:
        try:
            return _flatten(Image.open(io.BytesIO(blob))), ext
        except Exception:
            return None, ext
    if images:
        return max(images, key=lambda im: im.width * im.height), fmt
    return _inkscape_png(blob, "." + fmt), fmt + "-vector"


def save_png(image: Image.Image, path: Path) -> tuple[int, int]:
    if image.width > MAX_WIDTH:
        image = image.resize((MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return image.size
