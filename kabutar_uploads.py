"""Bounded readers for the two Kabutar message-upload endpoints.

Multipart bodies may already have been spooled by ASGI; this helper limits the
additional in-process read to the per-file limit plus one byte. An edge/server
request-body limit remains a separate deployment setting.
"""
import io

MIB = 1024 * 1024
KABUTAR_UPLOAD_LIMITS_MB = {"audio": 15, "video": 40, "video_doira": 40, "hujjat": 15}
READ_CHUNK_BYTES = 64 * 1024


class UploadTooLarge(ValueError):
    def __init__(self, max_bytes):
        self.max_bytes = max_bytes
        super().__init__(f"Fayl {max_bytes // MIB} MB dan katta")


async def read_bounded_upload(upload, max_bytes):
    """Return bytes or reject early; always close the UploadFile/temp file.

    ``UploadFile.size`` is Starlette's measured size, not Content-Length. If
    unavailable, read at most max_bytes + 1 bytes in bounded chunks and fail
    immediately once that boundary is crossed. Empty files return b'' for the
    endpoint's existing validation. Cancellation also runs cleanup.
    """
    buffer = io.BytesIO()
    try:
        if not isinstance(max_bytes, int) or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive integer")
        known_size = getattr(upload, "size", None)
        if isinstance(known_size, int) and known_size > max_bytes:
            raise UploadTooLarge(max_bytes)
        size = 0
        while True:
            block = await upload.read(min(READ_CHUNK_BYTES, max_bytes - size + 1))
            if not block:
                break
            size += len(block)
            if size > max_bytes:
                raise UploadTooLarge(max_bytes)
            buffer.write(block)
        return buffer.getvalue()
    finally:
        buffer.close()
        await upload.close()
