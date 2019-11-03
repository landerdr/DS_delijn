#!/bin/bash
sudo apt-get install python3-pip
pip3 install -r requirements.txt
xdg-open http://127.0.0.1:5000
python3 ./WebApp/webserver.py