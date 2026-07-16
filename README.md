# Proxy RNN Web Terminal

A self-updating web-based secure terminal for Flux nodes, featuring persistent sessions via `tmux`, VS Code CLI integrations, and credentials configuration via file or environment variables.

## How it Works

When deploying to a Flux node, encrypting environment variables like `TERMINAL_PASSWORD` typically requires a paid Enterprise subscription.

To work around this, this project allows you to load the password from a `credentials.json` file inside the container:
1. **Fallback Flow**: If the environment variable `TERMINAL_PASSWORD` is not set, the application looks for a `credentials.json` file inside the container.
2. **Supported Paths**: It searches in the following paths (in order):
   - `/app/credentials.json` (recommended path for Flux container deployments)
   - `/data/credentials.json`
   - `/appdata/credentials.json`
   - `./credentials.json` (the local directory)
3. **Format**: The file should contain a JSON object specifying the password (and optionally, the username):
   ```json
   {
     "username": "gen",
     "password": "your-secure-password"
   }
   ```
4. **Environment Precedence**: If `TERMINAL_PASSWORD` is provided via environment variables, the script will use it directly and bypass the file lookups.

---

## Configuration Variables

Configure your Flux node deployment using the following environment variables:

| Environment Variable | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `GIT_REPO_URL` | The URL of your repository containing the code. | `https://github.com/juand89/proxy-rnn-2` |
| `APP_PORT` | The port the web terminal binds to. | `8080` |
| `POLLING_INTERVAL` | The interval (in seconds) between update checks. | `86400` (24 hours) |
| `TERMINAL_USER` | The default username for logging into the terminal. | `gen` |
| `TERMINAL_PASSWORD` | **Leave this unset or empty** to load it from the credentials file. | *(blank)* |

---

## Setup Instructions

### Step 1: Deploy on Flux
Deploy your container to the Flux network with the following environment variables:
* `APP_PORT`: `8080`
* `TERMINAL_USER`: `gen`
* *Do not set `TERMINAL_PASSWORD`*

### Step 2: Create the `credentials.json` File
1. Go to your Flux Node Dashboard.
2. Access the **Shell** interface of your running container.
3. Create the `credentials.json` file at `/app/credentials.json` (or `/data/credentials.json` / `/appdata/credentials.json` if using mapped volumes) with the following content:
   ```json
   {
     "username": "gen",
     "password": "your-secure-password-here"
   }
   ```
   *Tip: You can use the container's shell to write the file:*
   ```bash
   echo '{"username": "gen", "password": "your-secure-password-here"}' > /app/credentials.json
   ```
4. Start or restart the container script. The boot script will read the password from this file and start the terminal on the port specified by `APP_PORT` (e.g. `8080`).
