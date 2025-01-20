import os
import subprocess
import boto3
import shutil
import logging
import runpod
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def runpod_handler(job):
    try:
        job_input = job["input"]
        required_fields = ["input_s3_url", "output_s3_bucket", "output_s3_key"]
        if not all(field in job_input for field in required_fields):
            return {"error": f"Missing required fields: {required_fields}"}

        input_dir = "/tmp/input_dir"
        output_dir = "/tmp/output_dir"
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        s3 = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        input_s3_url = job_input["input_s3_url"]
        parsed_url = urlparse(input_s3_url)
        input_bucket = parsed_url.netloc.split('.')[0]
        input_key = parsed_url.path.lstrip('/')

        raw_file = os.path.join(input_dir, "raw_input")
        input_file = os.path.join(input_dir, "input.wav")
        enhanced_file = os.path.join(output_dir, "input_enhanced.wav")

        try:
            logger.info(f"Downloading from s3://{input_bucket}/{input_key}")
            s3.download_file(input_bucket, input_key, raw_file)
        except Exception as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            return {"error": f"S3 download failed: {str(e)}"}

        try:
            logger.info("Converting to PCM WAV")
            subprocess.run(
                ["ffmpeg", "-i", raw_file, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", input_file],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr}")
            return {"error": f"FFmpeg conversion failed: {e.stderr}"}

        try:
            logger.info("Processing with resemble-enhance")
            result = subprocess.run(
                ["resemble-enhance", input_dir, output_dir],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Resemble-enhance output: {result.stdout}")
            logger.error(f"Resemble-enhance error: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Resemble-enhance processing failed: {e.stderr}")
            return {"error": f"Resemble-enhance processing failed: {e.stderr}"}

        if not os.path.exists(enhanced_file):
            logger.error("Enhanced file was not created by resemble-enhance.")
            return {"error": "Enhanced file was not created"}

        try:
            output_bucket = job_input["output_s3_bucket"]
            output_key = job_input["output_s3_key"]
            logger.info(f"Uploading to s3://{output_bucket}/{output_key}")
            s3.upload_file(enhanced_file, output_bucket, output_key)
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            return {"error": f"S3 upload failed: {str(e)}"}

        output_url = f"https://{output_bucket}.s3.amazonaws.com/{output_key}"

        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

        return {"status": "success", "output_url": output_url}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}

runpod.serverless.start({"handler": runpod_handler})
