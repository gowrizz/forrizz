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

        input_s3_url = job_input["input_s3_url"]
        parsed_url = urlparse(input_s3_url)
        input_bucket = parsed_url.netloc.split('.')[0]
        input_key = parsed_url.path.lstrip('/')

        input_file = os.path.join(input_dir, "input.wav")
        
        s3 = boto3.client('s3')
        logger.info(f"Downloading from s3://{input_bucket}/{input_key}")
        s3.download_file(input_bucket, input_key, input_file)

        logger.info("Processing with re")
        subprocess.run(["resemble-enhance", input_dir, output_dir], check=True)

        enhanced_file = os.path.join(output_dir, "input_enhanced.wav")
        if not os.path.exists(enhanced_file):
            return {"error": "Enhanced file was not created"}

        logger.info(f"Uploading to s3://{job_input['output_s3_bucket']}/{job_input['output_s3_key']}")
        s3.upload_file(enhanced_file, job_input['output_s3_bucket'], job_input['output_s3_key'])

        output_url = f"https://{job_input['output_s3_bucket']}.s3.amazonaws.com/{job_input['output_s3_key']}"
        shutil.rmtree(input_dir)
        shutil.rmtree(output_dir)

        return {"status": "success", "output_url": output_url}

    except Exception as e:
        logger.error(str(e))
        return {"error": str(e)}

runpod.serverless.start({"handler": runpod_handler})