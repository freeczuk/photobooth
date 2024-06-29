#!/bin/bash

# Enable the service
sudo systemctl enable photobooth.service

# Reload systemd configuration
sudo systemctl daemon-reload

# Start the service
sudo systemctl start photobooth.service

# Check the status to ensure it's running
sudo systemctl status photobooth.service
