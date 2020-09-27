#!/usr/bin/env python
import os
import boto3
import click
import pandas as pd


@click.command()
@click.option(
    "-k", "--s3-key",
)
def process_data(s3_key):
    print(f"Start process {s3_key}...")
    s3 = boto3.client("s3")

    # Download raw file from S3
    local_file = f"/tmp/{s3_key}"
    s3.download_file("my-raw-data", s3_key, local_file)

    # Process data
    df = pd.read_csv(local_file)
    for column in list("ABCD"):
        df[column] = df[column] + 100
    
    # Upload processed data to S3
    new_local_file = f"/tmp/new-{s3_key}"
    df.to_csv(new_local_file)
    s3.upload_file(new_local_file, "my-processed-data", f"new-{s3_key}")

    print("POSTGRES DATABASE:", os.environ["solar_POSTGRES_DB"])
    print("POSTGRES USER:", os.environ["solar_POSTGRES_USER"])
    print("Done!")


if __name__ == "__main__":
    process_data()
