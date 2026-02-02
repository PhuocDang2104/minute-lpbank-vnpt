"""
Supabase S3-compatible storage helper.

Uses boto3 with a custom endpoint to upload files and generate presigned URLs.
Falls back to returning None when storage is not configured.
"""
import io
import logging
import re
import uuid
from functools import lru_cache
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _slugify_filename(name: str) -> str:
    """Make a safe-ish filename segment."""
    name = name.strip().lower()
    # Replace any char not alnum, dot, dash, underscore with hyphen
    name = re.sub(r'[^a-z0-9._-]+', '-', name)
    # Collapse multiple hyphens
    name = re.sub(r'-{2,}', '-', name)
    name = name.strip('-_.')
    return name or "file"


def is_storage_configured() -> bool:
    """Check whether all required storage envs are present."""
    settings = get_settings()
    return all(
        [
            settings.supabase_s3_endpoint,
            settings.supabase_s3_region,
            settings.supabase_s3_bucket,
            settings.supabase_s3_access_key,
            settings.supabase_s3_secret_key,
        ]
    )


@lru_cache()
def _get_s3_client():
    """Create and cache a boto3 client for Supabase Storage."""
    if not is_storage_configured():
        return None
    settings = get_settings()
    session = boto3.session.Session(
        aws_access_key_id=settings.supabase_s3_access_key,
        aws_secret_access_key=settings.supabase_s3_secret_key,
        region_name=settings.supabase_s3_region,
    )
    return session.client(
        "s3",
        endpoint_url=settings.supabase_s3_endpoint,
        config=BotoConfig(signature_version="s3v4"),
    )


def build_object_key(filename: str, prefix: str = "uploads") -> str:
    """Build a unique object key for S3 storage."""
    stem, dot, ext = filename.rpartition(".")
    safe_name = _slugify_filename(stem or filename)
    ext_part = f".{ext}" if dot else ""
    return f"{prefix}/{uuid.uuid4()}_{safe_name}{ext_part}"


def upload_bytes_to_storage(
    data: bytes,
    object_key: str,
    content_type: Optional[str] = None,
) -> Optional[str]:
    """
    Upload bytes to Supabase Storage.
    
    Uses multipart upload for large files (automatically handled by boto3).
    For files larger than 64MB, boto3 automatically uses multipart upload.
    
    Returns the object key on success, or None if not configured.
    """
    if not is_storage_configured():
        logger.warning("Storage not configured; skipping upload.")
        return None
    client = _get_s3_client()
    if not client:
        return None
    settings = get_settings()
    try:
        file_size = len(data)
        
        # upload_fileobj automatically uses multipart upload for files > multipart_threshold
        # Default multipart_threshold is 8MB, which should work fine
        client.upload_fileobj(
            io.BytesIO(data),
            settings.supabase_s3_bucket,
            object_key,
            ExtraArgs={"ContentType": content_type or "application/octet-stream"},
        )
        logger.info(f"Successfully uploaded {file_size / (1024*1024):.2f}MB to {object_key}")
        return object_key
    except (BotoCoreError, NoCredentialsError, ClientError) as exc:
        logger.error("Failed to upload to storage: %s", exc)
        # Provide more helpful error message
        if "EntityTooLarge" in str(exc):
            raise RuntimeError(
                f"File is too large for storage. "
                f"Current file size: {len(data) / (1024*1024):.2f}MB. "
                f"Supabase Storage might have size limits. Consider compressing the video or using direct upload."
            ) from exc
        raise


def generate_presigned_get_url(object_key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a presigned GET URL for an object."""
    if not is_storage_configured():
        return None
    client = _get_s3_client()
    if not client:
        return None
    settings = get_settings()
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.supabase_s3_bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("Failed to generate presigned URL: %s", exc)
        return None


def delete_object(object_key: str) -> bool:
    """Delete an object from storage bucket. Returns True on success/skip."""
    if not is_storage_configured():
        return False
    client = _get_s3_client()
    if not client:
        return False
    settings = get_settings()
    try:
        client.delete_object(Bucket=settings.supabase_s3_bucket, Key=object_key)
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.error("Failed to delete object %s: %s", object_key, exc)
        return False
