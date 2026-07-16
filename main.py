import os
import subprocess
import urllib.request
import sys
import json
import secrets
import urllib.parse
import http.server
import socketserver
import threading

class SetupHandler(http.server.BaseHTTPRequestHandler):
    setup_token = None
    credentials_file = "credentials.json"
    server_instance = None

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        token = params.get("token", [None])[0]
        
        if not self.setup_token or token != self.setup_token:
            self.send_response(403)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Forbidden: Invalid or missing setup token. Check container logs.")
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Terminal Setup</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background: linear-gradient(135deg, #121214 0%, #1a1a24 100%);
                    color: #e0e0e0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background: rgba(30, 30, 40, 0.85);
                    backdrop-filter: blur(10px);
                    padding: 40px;
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                    width: 320px;
                }}
                h2 {{ 
                    margin-top: 0; 
                    color: #ffffff; 
                    text-align: center; 
                    font-weight: 600;
                    margin-bottom: 24px;
                }}
                label {{ 
                    display: block; 
                    margin-top: 18px; 
                    margin-bottom: 6px; 
                    font-size: 14px;
                    color: #a0a0b0;
                }}
                input[type="text"], input[type="password"] {{
                    width: 100%;
                    padding: 10px 12px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    background-color: rgba(0, 0, 0, 0.2);
                    color: #fff;
                    border-radius: 6px;
                    box-sizing: border-box;
                    transition: border-color 0.2s;
                }}
                input[type="text"]:focus, input[type="password"]:focus {{
                    border-color: #007acc;
                    outline: none;
                }}
                button {{
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, #007acc 0%, #005999 100%);
                    border: none;
                    color: white;
                    border-radius: 6px;
                    margin-top: 28px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 15px;
                    box-shadow: 0 4px 12px rgba(0, 122, 204, 0.3);
                    transition: opacity 0.2s;
                }}
                button:hover {{ 
                    opacity: 0.95;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Terminal Setup</h2>
                <form method="POST" action="/save?token={token}">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required value="admin">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required placeholder="Choose a secure password">
                    <button type="submit">Save & Start Terminal</button>
                </form>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        token = params.get("token", [None])[0]
        
        if not self.setup_token or token != self.setup_token:
            self.send_response(403)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Forbidden: Invalid token.")
            return

        if parsed_url.path == "/save":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            fields = urllib.parse.parse_qs(post_data)
            
            username = fields.get("username", ["admin"])[0]
            password = fields.get("password", [""])[0]
            
            if not password:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Password cannot be empty.")
                return
            
            # Save credentials
            with open(self.credentials_file, "w") as f:
                json.dump({"username": username, "password": password}, f)
                
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body style="background:#121214; color:#e0e0e0; font-family:sans-serif; text-align:center; padding-top:100px;">
                <h2>Setup Complete!</h2>
                <p>Credentials saved. The terminal is starting now.</p>
                <p>Please wait a few seconds, then <a href="/" style="color:#007acc; text-decoration:none; font-weight:bold;">Refresh Page</a> to log in.</p>
            </body>
            </html>
            """)
            
            # Stop the server in a separate thread so we can complete this response first
            def shutdown_server():
                self.server_instance.shutdown()
            threading.Thread(target=shutdown_server).start()

class ReuseAddrHTTPServer(socketserver.TCPServer):
    allow_reuse_address = True

def start_terminal():
    ttyd_path = "/tmp/ttyd"
    
    # 1. Download ttyd binary
    print("Downloading ttyd (Web Terminal)...")
    try:
        urllib.request.urlretrieve("https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.x86_64", ttyd_path)
        os.chmod(ttyd_path, 0o755)
    except Exception as e:
        print(f"Error downloading ttyd: {e}")
        sys.exit(1)

    tmux_path = "/tmp/tmux"
    print("Downloading tmux...")
    try:
        urllib.request.urlretrieve("https://github.com/pythops/tmux-linux-binary/releases/download/v3.6a/tmux-linux-x86_64", tmux_path)
        os.chmod(tmux_path, 0o755)
    except Exception as e:
        print(f"Error downloading tmux: {e}")
        sys.exit(1)

    print("Downloading GitHub CLI (gh)...")
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
        print(f"Error downloading gh: {e}")
        # We don't exit here because gh is optional, but it's good to know if it failed.

    print("Downloading VS Code CLI...")
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
        print(f"Error downloading VS Code CLI: {e}")

    # Add /tmp to PATH so that gh and tmux can be executed just by typing their names
    os.environ["PATH"] = f"/tmp:{os.environ.get('PATH', '')}"

    # 2. Get port and credentials
    port_env = os.environ.get("APP_PORT", "8080")
    try:
        port = int(port_env)
    except ValueError:
        print(f"Invalid APP_PORT: {port_env}. Defaulting to 8080.")
        port = 8080

    user = os.environ.get("TERMINAL_USER")
    password = os.environ.get("TERMINAL_PASSWORD")

    if not password:
        credentials_file = "credentials.json"
        if os.path.exists("/data") and os.path.isdir("/data"):
            credentials_file = "/data/credentials.json"
            
        if os.path.exists(credentials_file):
            try:
                with open(credentials_file, "r") as f:
                    creds = json.load(f)
                    user = creds.get("username", "admin")
                    password = creds.get("password")
            except Exception as e:
                print(f"Error reading credentials file: {e}")
        
        if not password:
            setup_token = secrets.token_hex(16)
            SetupHandler.setup_token = setup_token
            SetupHandler.credentials_file = credentials_file
            
            server = ReuseAddrHTTPServer(("", port), SetupHandler)
            SetupHandler.server_instance = server
            
            print("\n" + "="*80)
            print(" ACTION REQUIRED: SECURE SETUP REQUIRED")
            print(f" Please visit: http://<your-flux-node-ip>:{port}/?token={setup_token}")
            print(" Enter the username and password you want to use for the terminal.")
            print("="*80 + "\n")
            sys.stdout.flush()
            
            server.serve_forever()
            
            # Reload credentials after server shutdown
            try:
                with open(credentials_file, "r") as f:
                    creds = json.load(f)
                    user = creds.get("username", "admin")
                    password = creds.get("password")
            except Exception as e:
                print(f"Error reading credentials file after setup: {e}")
                sys.exit(1)

    if not user:
        user = "admin"

    # 3. Start the terminal
    print(f"Starting secure terminal on port {port}...")
    
    # -W: writable (allow typing commands)
    # -p <port>: port
    # -c user:password: basic auth
    # bash: the shell to run
    # We replace bash with our downloaded tmux binary to maintain persistent sessions
    subprocess.run([ttyd_path, "-W", "-p", str(port), "-c", f"{user}:{password}", tmux_path, "new-session", "-A", "-s", "web_session"])


if __name__ == "__main__":
    start_terminal()
