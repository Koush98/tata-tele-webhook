#!/usr/bin/env bash

# Update package list
apt-get update

# Install dependencies for ODBC
apt-get install -y curl apt-transport-https software-properties-common unixodbc-dev

# Add Microsoft package repository
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update again and install ODBC Driver 18
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # ✅ Ensure gunicorn is installed
