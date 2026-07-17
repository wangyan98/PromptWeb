import json
import uuid
from io import BytesIO
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from app.config import settings


class MinioService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self.bucket = settings.minio_bucket

    async def ensure_bucket(self):
        found = self.client.bucket_exists(self.bucket)
        if not found:
            self.client.make_bucket(self.bucket)
            # Set public read policy
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
                    }
                ],
            }
            self.client.set_bucket_policy(self.bucket, json.dumps(policy))

    async def upload(self, file: UploadFile, prompt_id: int) -> str:
        ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "png"
        object_name = f"{prompt_id}/{uuid.uuid4()}.{ext}"
        content = await file.read()
        file.file.seek(0)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=BytesIO(content),
            length=len(content),
            content_type=file.content_type or "image/png",
        )
        return f"/api/images/file/{object_name}"

    def delete(self, object_name: str):
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error:
            pass

    def get_object_name_from_url(self, url: str) -> str:
        # URL format: /api/images/file/prompt-images/1/uuid.png
        prefix = f"/api/images/file/"
        if url.startswith(prefix):
            return url[len(prefix):]
        return url


minio_service = MinioService()
