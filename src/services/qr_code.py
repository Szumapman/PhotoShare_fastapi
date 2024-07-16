import io

import qrcode
from fastapi.responses import StreamingResponse

from src.services.abstract import AbstractQrCodeProvider


class QrCodeProvider(AbstractQrCodeProvider):
    """
    This class is an implementation of the AbstractQrCodeProvider interface to use with the qrcode library.
    """
    async def stream_qr_code(self, url: str):
        """
        Streams QR code image for provided url

        :param url: url to create QR code for
        :type url: str
        :return: StreamingResponse object with QR code image
        :rtype: StreamingResponse
        """
        qr_code_img = qrcode.make(url)
        buffer = io.BytesIO()
        qr_code_img.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png")
