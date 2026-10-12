#!/usr/bin/env python3
import aws_cdk as cdk
from stack import HiveMindStack

app = cdk.App()
HiveMindStack(app, "HiveMind")
app.synth()
