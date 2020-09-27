import boto3


def submit_jobs():
    """Submit jobs via boto3"""

    client = boto3.client("batch")

    for i, name in enumerate(["file1.csv", "file2.csv", "file3.csv"]):
        client.submit_job(
            jobName=f"my-job-{i+1}",
            jobQueue="solar-job-queue",
            jobDefinition="solar-job-definition",
            containerOverrides={
                "command": ["python", "process_data.py", "--s3-key", name]
            }
        )


if __name__ == "__main__":
    submit_jobs()
