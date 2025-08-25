import io
import os
from uuid import uuid4

from decouple import config
from fastapi import HTTPException, UploadFile, status
from minio import Minio


class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=f"{config('MINIO_ENDPOINT')}",
            access_key=config("MINIO_ACCESS_KEY", default="eurekaminioadmin"),
            secret_key=config("MINIO_SECRET_KEY", default="eurekaminioadmin"),
            secure=config("MINIO_SECURE", cast=bool),
        )
        self.bucket_name = config("MINIO_BUCKET", default="eureka-bucket")

        self.create_bucket()

    def create_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    async def upload_file(self, file: UploadFile) -> str:

        try:
            exists = self.client.bucket_exists(self.bucket_name)

            if not exists:
                self.client.make_bucket(self.bucket_name)
            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid4().hex}{ext}"
            file_content = await file.read()
            file_size = len(file_content)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=file.content_type or 'application/octet-stream'
            )
            return unique_filename
        except Exception as e:
            self._exception(f"Error while uploading file: {e}")

    def download_file(self, object_name: str):
        try:
            return self.client.get_object(self.bucket_name, object_name)
        except Exception as e:
            self._exception(f"Error while downloading file: {e}")

    def get_file_url(self, object_name: str):
        return self.client.presigned_get_object(
            self.bucket_name, object_name=object_name
        )

    def _exception(self, detail: str):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


minio_client = MinioClient()
