#!/usr/bin/env python3

from aws_cdk import core

from batch.stack import AWSBatchStack, STACK_PREFIX


app = core.App()
AWSBatchStack(app, f"{STACK_PREFIX}-batch-stack")

app.synth()
