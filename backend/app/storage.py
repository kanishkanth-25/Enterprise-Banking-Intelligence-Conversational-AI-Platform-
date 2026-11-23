from app.config import GCS_BUCKET_NAME


def store_upload(data: bytes, object_name: str, content_type: str | None) -> str | None:
    if not GCS_BUCKET_NAME:
        return None
    from google.cloud import storage

    blob = storage.Client().bucket(GCS_BUCKET_NAME).blob(object_name)
    blob.upload_from_string(data, content_type=content_type)
    return f"gs://{GCS_BUCKET_NAME}/{object_name}"
