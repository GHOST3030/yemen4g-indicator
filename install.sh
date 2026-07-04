#!/bin/bash
echo "=========================================="
echo "  Yemen 4G Indicator Setup & Launcher  Built by: @GHOST3030" "
echo "=========================================="
echo ""
echo "Installing required dependencies..."
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7 python3-requests python3-bs4

echo ""
echo "Making the script executable..."
chmod +x yemen4g_github.py

echo "Starting Yemen 4G Indicator..."
# Run the script in the background so the terminal can be closed
nohup python3 yemen4g_github.py > /dev/null 2>&1 &

echo "Done! The indicator should now appear in your system tray."
