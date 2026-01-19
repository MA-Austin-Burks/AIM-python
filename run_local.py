#!/usr/bin/env python3
"""Wrapper script to run Streamlit app in local mode.

Usage:
    python run_local.py
    python run_local.py --server.port 8502
"""
import os
import sys
import subprocess

# Set environment variable for local mode
os.environ["USE_LOCAL_DATA"] = "true"

# Run streamlit with remaining arguments
cmd = ["streamlit", "run", "app.py"] + sys.argv[1:]
subprocess.run(cmd)
