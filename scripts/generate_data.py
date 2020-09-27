import os
import boto3
import numpy as np
import pandas as pd


def generate():
    """Generate sample CSV files and upload to S3 bucket"""
    
    for name in ["file1.csv", "file2.csv", "file3.csv"]:
        filename = f"/tmp/{name}"

        dates = pd.date_range("20120105", periods=6)
        df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list("ABCD"))
        df.to_csv(filename)

        try:
            s3 = boto3.client("s3")
            s3.upload_file(filename, "my-raw-data", name)
        finally:
            os.remove(filename)


if __name__ == "__main__":
    generate()
