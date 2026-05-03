import os
import subprocess
import urllib.request
import sys

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

    # 2. Get credentials from environment variables
    user = os.environ.get("TERMINAL_USER", "admin")
    password = os.environ.get("TERMINAL_PASSWORD", "password")

    # Add /tmp to PATH so that gh and tmux can be executed just by typing their names
    os.environ["PATH"] = f"/tmp:{os.environ.get('PATH', '')}"

    # 3. Start the terminal
    print("Starting secure terminal on port 8080...")
    
    # -W: writable (allow typing commands)
    # -p 8080: port
    # -c user:password: basic auth
    # bash: the shell to run
    # We replace bash with our downloaded tmux binary to maintain persistent sessions
    subprocess.run([ttyd_path, "-W", "-p", "8080", "-c", f"{user}:{password}", tmux_path, "new-session", "-A", "-s", "web_session"])


if __name__ == "__main__":
    start_terminal()
