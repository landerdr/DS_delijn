#!/bin/bash
pip3 install -r requirements.txt
python3 ./WebApp/webserver.py
xdg-open http://127.0.0.1:5000