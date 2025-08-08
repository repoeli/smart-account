"""
Cloudinary storage adapter implementing StorageProvider port.
"""

from __future__ import annotations

import cloudinary
import cloudinary.uploader
from typing import Optional
from django.conf import settings

from application.receipts.ports import StorageProvider, StoredAsset


class CloudinaryStorageAdapter(StorageProvider):
    def __init__(self):
        cloudinary.config(
            cloud_name=getattr(settings, "CLOUDINARY_CLOUD_NAME", None),
            api_key=getattr(settings, "CLOUDINARY_API_KEY", None),
            api_secret=getattr(settings, "CLOUDINARY_API_SECRET", None),
            secure=True,
        )
        self.folder = getattr(settings, "CLOUDINARY_RECEIPTS_FOLDER", "receipts")

    def upload(self, *, file_bytes: bytes, filename: str, mime: Optional[str] = None) -> StoredAsset:
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=self.folder,
            resource_type="image",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            public_id=None,
        )
        return StoredAsset(
            public_id=result.get("public_id"),
            secure_url=result.get("secure_url"),
            width=result.get("width"),
            height=result.get("height"),
            bytes=result.get("bytes"),
            format=result.get("format"),
        )


