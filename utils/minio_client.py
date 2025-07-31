import io
import os
from uuid import uuid4

from decouple import config
from fastapi import HTTPException, UploadFile, status
from minio import Minio


class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=f'{config("MINIO_ENDPOINT")}:{config("PORT")}',
            access_key=config("MINIO_ACCESS_KEY", default="minioadmin"),
            secret_key=config("MINIO_SECRET_KEY", default="minioadmin"),
            secure=config("MINIO_SECURE", default="false", cast=bool),
        )
        self.bucket_name = config("MINIO_BUCKET", default="minio-bucket")

    def create_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    async def upload_file(self, file: UploadFile) -> str:
        self.create_bucket()
        try:
            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid4().hex}{ext}"

            contents = await file.read()
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=io.BytesIO(contents),
                length=len(contents),
                content_type=file.content_type,
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
