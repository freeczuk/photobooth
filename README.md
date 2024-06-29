# Photobooth

Code for interactive Photobooth that is controlled via wireless numerical keyboard.

**HW requirements:**
- Raspberry Pi version 3B+ or newer
- Camera module V3 (_code is not compatible with older version_)
- Canon printer CP1500
- Screen 1920x1080 (resolution is fixed)

**Instructions:**
- Main entry point is `run_booth.py`, running infinite loop
- Set this up as service, using `photobooth.service`
  - Move `photobooth.service` to  `/etc/systemd/system`
  - Start the service
      ``` 
      sudo systemctl daemon-reload
      sudo systemctl enable photobooth.service
      sudo systemctl start photobooth.service
      ```
    
