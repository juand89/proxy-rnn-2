import os
import subprocess
import urllib.request
import sys
import json

def start_terminal():
    # Force stdout/stderr to be unbuffered to ensure logs appear immediately in Flux dashboard
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except (AttributeError, TypeError):
        pass

    print("Proxy RNN: Initializing secure boot...", flush=True)

    # 1. Determine credentials file path (supporting /app, /data, or /appdata volumes)
    credentials_file = "credentials.json"
    if os.path.exists("/app") and os.path.isdir("/app"):
        credentials_file = "/app/credentials.json"
    elif os.path.exists("/data") and os.path.isdir("/data"):
        credentials_file = "/data/credentials.json"
    elif os.path.exists("/appdata") and os.path.isdir("/appdata"):
        credentials_file = "/appdata/credentials.json"

    # 2. Get port and credentials
    port_env = os.environ.get("APP_PORT", "8080")
    try:
        port = int(port_env)
    except ValueError:
        print(f"Invalid APP_PORT: {port_env}. Defaulting to 8080.", flush=True)
        port = 8080

    user = os.environ.get("TERMINAL_USER")
    password = os.environ.get("TERMINAL_PASSWORD")

    # If password is not provided in environment variables, try to load it from credentials file
    if not password:
        if os.path.exists(credentials_file):
            try:
                with open(credentials_file, "r") as f:
                    creds = json.load(f)
                    # Use username from JSON if not explicitly provided in environment
                    if not user:
                        user = creds.get("username")
                    password = creds.get("password")
            except Exception as e:
                print(f"Error reading credentials file: {e}", flush=True)
        else:
            print(f"Warning: credentials file not found at {credentials_file}", flush=True)

        if not password:
            print(f"Error: No TERMINAL_PASSWORD set and could not load from {credentials_file}.", flush=True)
            print("Please set TERMINAL_PASSWORD environment variable or create the credentials.json file.", flush=True)
            sys.exit(1)

    if not user:
        user = "admin"

    # 3. Download binaries (only after credentials are verified/set)
    ttyd_path = "/tmp/ttyd"
    print("Downloading ttyd (Web Terminal)...", flush=True)
    try:
        urllib.request.urlretrieve("https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.x86_64", ttyd_path)
        os.chmod(ttyd_path, 0o755)
    except Exception as e:
        print(f"Error downloading ttyd: {e}", flush=True)
        sys.exit(1)

    tmux_path = "/tmp/tmux"
    print("Downloading tmux...", flush=True)
    try:
        urllib.request.urlretrieve("https://github.com/pythops/tmux-linux-binary/releases/download/v3.6a/tmux-linux-x86_64", tmux_path)
        os.chmod(tmux_path, 0o755)
    except Exception as e:
        print(f"Error downloading tmux: {e}", flush=True)
        sys.exit(1)

    print("Downloading GitHub CLI (gh)...", flush=True)
    try:
        import tarfile
        gh_tar_path = "/tmp/gh.tar.gz"
        urllib.request.urlretrieve("https://github.com/cli/cli/releases/download/v2.92.0/gh_2.92.0_linux_amd64.tar.gz", gh_tar_path)
        with tarfile.open(gh_tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("/bin/gh"):
                    member.name = "gh"  # Strip directories, extract directly to path
                    tar.extract(member, path="/tmp")
                    break
        os.chmod("/tmp/gh", 0o755)
    except Exception as e:
        print(f"Error downloading gh: {e}", flush=True)

    print("Downloading VS Code CLI...", flush=True)
    try:
        code_tar_path = "/tmp/code.tar.gz"
        urllib.request.urlretrieve("https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64", code_tar_path)
        with tarfile.open(code_tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name == "code":
                    tar.extract(member, path="/tmp")
                    break
        os.chmod("/tmp/code", 0o755)
    except Exception as e:
        print(f"Error downloading VS Code CLI: {e}", flush=True)

    # Add /tmp to PATH so that gh and tmux can be executed just by typing their names
    os.environ["PATH"] = f"/tmp:{os.environ.get('PATH', '')}"

    # 4. Start the terminal
    print(f"Starting secure terminal on port {port}...", flush=True)
    
    # -W: writable (allow typing commands)
    # -p <port>: port
    # -c user:password: basic auth
    # bash: the shell to run
    # We replace bash with our downloaded tmux binary to maintain persistent sessions
    subprocess.run([ttyd_path, "-W", "-p", str(port), "-c", f"{user}:{password}", tmux_path, "new-session", "-A", "-s", "web_session"])


if __name__ == "__main__":
    start_terminal()
