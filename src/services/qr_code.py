import io

import qrcode
from fastapi.responses import StreamingResponse

from src.services.abstract import AbstractQrCodeProvider


class QrCodeProvider(AbstractQrCodeProvider):
    async def stream_qr_code(self, url: str):
        qr_code_img = qrcode.make(url)
        buffer = io.BytesIO()
        qr_code_img.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png")
