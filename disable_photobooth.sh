#!/bin/bash

# Stop the service if it's running
sudo systemctl stop photobooth.service

# Disable the service
sudo systemctl disable photobooth.service

# Reload systemd configuration
sudo systemctl daemon-reload

# Check the status to ensure it's disabled
sudo systemctl status photobooth.service
