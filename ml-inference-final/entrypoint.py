import os
import json
import tempfile
import subprocess
import boto3
from pathlib import Path
import tarfile


def download_directory_from_s3(bucket: str, prefix: str, target_dir: Path):
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue

            local_path = target_dir / key.replace(prefix + "/", "")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, key, str(local_path))


def create_tar_from_dir(source_dir: Path, tar_path: Path):
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(source_dir, arcname=".")


def main():
    bucket = os.environ["BENTO_S3_BUCKET"]
    prefix_base = os.environ["BENTO_S3_PREFIX"]
    stage = os.environ["BENTOML_MODEL_STAGE"]

    print(f"[INFO] Starting inference in stage={stage}")

    pointer_key = f"{prefix_base}/{stage}"
    s3 = boto3.client("s3")

    print(f"[INFO] Resolving model pointer s3://{bucket}/{pointer_key}")
    obj = s3.get_object(Bucket=bucket, Key=pointer_key)
    pointer = json.loads(obj["Body"].read())

    model_prefix = pointer["bento_s3_prefix"]
    print(f"[INFO] Model artifact prefix={model_prefix}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        download_root = tmp_path / "model"
        tar_path = tmp_path / "model.tar.gz"

        print(f"[INFO] Downloading Bento directory to {download_root}")
        download_directory_from_s3(
            bucket=bucket,
            prefix=model_prefix,
            target_dir=download_root,
        )

        print(f"[INFO] Creating tar archive {tar_path}")
        create_tar_from_dir(download_root, tar_path)

        print("[INFO] Importing Bento model")
        subprocess.check_call([
            "bentoml", "models", "import", str(tar_path)
        ])

    print("[INFO] Starting BentoML server")

    subprocess.check_call([
        "bentoml",
        "serve",
        "service:svc",
        "--host", "0.0.0.0",
        "--port", "3000",
    ])


if __name__ == "__main__":
    main()
