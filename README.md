# Proxy RNN Web Terminal

A self-updating web-based secure terminal for Flux nodes, featuring persistent sessions via `tmux`, VS Code CLI integrations, and an automated secure credentials configuration flow.

## How it Works

When deploying to a Flux node, encrypting environment variables like `TERMINAL_PASSWORD` typically requires a paid Enterprise subscription. 

To work around this, this project includes a secure, interactive setup server:
1. **Unset Password Check**: If the environment variable `TERMINAL_PASSWORD` is omitted, the application runs a lightweight setup wizard on the same port defined by `APP_PORT` (default `8080`).
2. **One-Time Setup Token**: The server generates a random, cryptographically secure token and prints the setup URL (e.g. `http://<flux-node-ip>:8080/?token=abc123xyz...`) directly to the container's standard output (stdout). Only you can see this setup URL in the Flux logs dashboard.
3. **Interactive Configuration**: Visiting the setup URL opens a secure interface where you can specify your terminal username and password.
4. **Persistent Credentials**: Upon form submission, the credentials are saved to `credentials.json` (preferring `/data/credentials.json` if a persistent `/data` volume is mounted), the setup server shuts down, and the secure web terminal starts up on the same port.
5. **Auto-bypass**: On subsequent boots, the script detects the saved credentials file, bypasses the setup wizard entirely, and immediately starts the secure terminal.

---

## Configuration Variables

Configure your Flux node deployment using the following environment variables:

| Environment Variable | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `GIT_REPO_URL` | The URL of your repository containing the code. | `https://github.com/juand89/proxy-rnn-2` |
| `APP_PORT` | The port the terminal and setup wizard bind to. | `8080` |
| `POLLING_INTERVAL` | The interval (in seconds) between update checks. | `86400` (24 hours) |
| `TERMINAL_USER` | The default/preferred username for the terminal. | `gen` |
| `TERMINAL_PASSWORD` | **Leave this unset or empty** to activate the secure interactive setup flow. | *(blank)* |

---

## Setup Instructions

### Step 1: Deploy on Flux
Deploy your container to the Flux network with the following environment variables configured:
* `APP_PORT`: `8080`
* `TERMINAL_USER`: `gen`
* *Do not set `TERMINAL_PASSWORD`*

### Step 2: Retrieve the Setup Token
1. Go to your Flux Dashboard.
2. Select your running application and click **Logs**.
3. Look for the printout block resembling:
   ```text
   ================================================================================
    ACTION REQUIRED: SECURE SETUP REQUIRED
    Please visit: http://<your-flux-node-ip>:8080/?token=8e93ad38bc2fb4d5218d6a7df75b31d0
    Enter the username and password you want to use for the terminal.
   ================================================================================
   ```
4. Copy the URL.

### Step 3: Configure Your Credentials
1. Open the copied URL in your web browser.
2. Enter your desired **Username** (defaults to `gen` if configured in the environment variables) and set a secure **Password**.
3. Click **Save & Start Terminal**.
4. The setup page will confirm the save. Wait 5-10 seconds, then refresh the page (or go to `http://<your-flux-node-ip>:8080/`).
5. Log in using the credentials you just configured.

---

## Persistent Storage (Highly Recommended)
If you restart your container or update the deployment, the local `credentials.json` file will be lost if your container has no persistent volume. 

To keep your password persistent across restarts:
1. Mount a persistent volume at path `/data` or `/appdata` inside your Flux container settings.
2. The setup script automatically detects the presence of `/data` or `/appdata` and saves your credentials to `<volume_path>/credentials.json`.
3. If one of these volumes is mounted, you will only have to run this setup wizard **once**. If no volume is mounted, you will need to re-run the setup page and get a new token from the logs every time the container restarts.
