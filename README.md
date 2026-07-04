# Yemen 4G Balance Indicator 📶

A lightweight, automated system tray indicator for Linux (GNOME/GTK) that silently fetches and displays your Yemen 4G (PTC) internet balance right on your desktop panel.

![Yemen 4G Indicator](https://ptc.gov.ye/wp-content/uploads/2022/02/yemen4g-logo.png)

## Features ✨
- **Live Balance:** Always see your remaining GBs in the system tray.
- **Altcha PoW Solver:** Bypasses the website's new Altcha security system entirely in the background—no more typing captchas manually!
- **Auto-Refresh:** Configurable automatic refreshing. Choose between:
  - Every 15 minutes
  - Every 30 minutes
  - Every 1 hour
  - Manual only
- **Secure Configuration:** Prompts you for your phone number once on startup and saves it (along with your refresh interval preference) securely in a local JSON config file (`~/.yemen4g_config`).
- **Notifications:** View your full balance and expiration date instantly as a native desktop notification.

## Prerequisites 🛠️
This app is designed for GNOME-based Linux distributions (like Ubuntu, Zorin OS, Pop!_OS, Debian, etc).

Install the required Python and GTK dependencies by running this command in your terminal:
```bash
sudo apt update && sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7 python3-requests python3-bs4
```
*(If your system uses older AppIndicators, `gir1.2-appindicator3-0.1` will work as a fallback automatically).*

## Usage 🚀
1. Clone this repository or download the `yemen4g_github.py` file.
2. Make it executable:
   ```bash
   chmod +x yemen4g_github.py
   ```
3. Run the script:
   ```bash
   python3 yemen4g_github.py
   ```
4. **On the first launch**, a dialog will ask you for your Yemen 4G phone number. Enter it and click OK.
5. The indicator will appear in your top bar showing `4G: Fetching...` and will automatically solve the Altcha challenge to retrieve your balance.
6. Right-click the indicator to access the menu where you can:
   - Change your refresh interval.
   - Show full details (Date of expiration).
   - Change the phone number.

### Autostart on Boot (Optional)
To have the indicator run automatically when you log in:
1. Open "Startup Applications" on your Linux desktop.
2. Add a new program.
3. Set the Name to `Yemen 4G Indicator`.
4. Set the Command to: `python3 /absolute/path/to/yemen4g_github.py`
5. Save and you're good to go!

## How it Works 🧠
The PTC website recently switched from traditional image captchas to **Altcha**, a Proof-of-Work anti-bot system. This Python script fetches the Altcha challenge JSON, uses `hashlib.sha256` to brute-force the correct nonce (salt + number), generates the Base64 payload, and submits the form silently to retrieve your real-time balance.

## License
MIT License
