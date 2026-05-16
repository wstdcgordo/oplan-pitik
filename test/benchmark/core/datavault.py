import time
import platform
import subprocess
import mariadb

class DatabaseServiceManager:
    """
    Handles starting and waiting for a local MariaDB service.
    OS‑aware: supports macOS (brew), Linux (systemd/service), Windows (sc/net).
    """
    
    @staticmethod
    def ensure_running():
        """
        Detect OS and start MariaDB if not already running.
        Returns True if service is (now) running, False otherwise.
        """
        system = platform.system()
        try:
            if system == "Darwin":      # macOS
                status = subprocess.run(
                    ["brew", "services", "info", "mariadb"],
                    capture_output=True, text=True
                )
                if "started" not in status.stdout.lower():
                    print("Starting MariaDB via brew services...")
                    subprocess.run(["brew", "services", "start", "mariadb"], check=True)
                else:
                    print("MariaDB is already running.")
                return True

            elif system == "Linux":
                try:
                    status = subprocess.run(
                        ["systemctl", "is-active", "mariadb"],
                        capture_output=True, text=True
                    )
                    if status.returncode != 0 or "inactive" in status.stdout.lower():
                        print("Starting MariaDB via systemctl...")
                        subprocess.run(["sudo", "systemctl", "start", "mariadb"], check=True)
                    else:
                        print("MariaDB is already running.")
                    return True
                except FileNotFoundError:
                    status = subprocess.run(
                        ["service", "mariadb", "status"],
                        capture_output=True, text=True
                    )
                    if "running" not in status.stdout.lower():
                        print("Starting MariaDB via service...")
                        subprocess.run(["sudo", "service", "mariadb", "start"], check=True)
                    else:
                        print("MariaDB is already running.")
                    return True

            elif system == "Windows":
                result = subprocess.run(
                    ["sc", "query", "MariaDB"],
                    capture_output=True, text=True
                )
                if "RUNNING" not in result.stdout:
                    print("Starting MariaDB service on Windows...")
                    subprocess.run(["net", "start", "MariaDB"], check=True)
                else:
                    print("MariaDB service is already running.")
                return True

            else:
                print(f"Unsupported OS: {system}. Please start MariaDB manually.")
                return False

        except Exception as e:
            print(f"Warning: Could not start MariaDB automatically: {e}")
            return False

    @staticmethod
    def wait_until_ready(host, port, user, password, max_wait_seconds=15, check_interval=2):
        """
        Wait for MariaDB to accept connections.
        Returns True if ready within timeout, False otherwise.
        """
        print(f"⏳ Waiting for MariaDB to be ready (max {max_wait_seconds}s)...")
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                test_conn = mariadb.connect(
                    host=host, port=port, user=user, password=password
                )
                test_conn.close()
                print("✅ MariaDB is ready!")
                return True
            except mariadb.Error as e:
                if "Can't connect" in str(e) or "Connection refused" in str(e):
                    time.sleep(check_interval)
                    continue
                else:
                    # Other error – assume DB is reachable but config may be wrong
                    print("⚠️ Database reachable but other error occurred.")
                    return True
        print("❌ Timeout: MariaDB did not become ready in time.")
        return False