#!/bin/bash
chromium http://localhost:8000/demo.html
cd ..
python3 -m http.server