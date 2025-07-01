#!/bin/bash

# Exit on any error
set -e
apt update
echo "Starting setup process..."

# Install required system packages
echo "Installing python3.10-venv..."
sudo apt install python3.10-venv -y 

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate  

# Install Python dependencies
echo "Installing Python requirements..."
pip install -r requirements.txt


# Install Redis
echo "Installing Redis..."
sudo apt-get install lsb-release curl gpg -y
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
sudo chmod 644 /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis -y

echo "Setup completed successfully!"