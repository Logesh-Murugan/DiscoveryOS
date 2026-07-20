#!/usr/bin/env python
"""Test the ingestion API endpoint."""

import requests
import json

# Test files
files = [
    ("files", open("sample_data/interview_acme_corp.txt", "rb")),
    ("files", open("sample_data/interview_startup_labs.txt", "rb")),
    ("files", open("sample_data/support_tickets.csv", "rb")),
]

try:
    response = requests.post("http://127.0.0.1:8000/ingest/", files=files)
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, default=str)}")
    
    if response.status_code == 200:
        print(f"\nSuccess! Ingested {len(data.get('sources', []))} sources")
    
finally:
    for _, f in files:
        f.close()
