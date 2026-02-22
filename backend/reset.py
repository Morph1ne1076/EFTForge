import os
import subprocess
import time
import sys

DB_FILE = "tarkov.db"


def delete_db():
    if os.path.exists(DB_FILE):
        print("Deleting old database...")
        os.remove(DB_FILE)
    else:
        print("No existing database found.")


def sync_tarkov():
    print("Syncing tarkov.dev data...")
    subprocess.run([sys.executable, "sync_tarkov_dev.py"], check=True)


def seed_other():
    # Add any additional seed scripts here
    # subprocess.run(["python", "other_seed_script.py"], check=True)
    print("No additional seeds configured.")


def start_server():
    print("Starting server...")
    subprocess.run(["uvicorn", "main:app", "--reload"])


if __name__ == "__main__":
    delete_db()
    sync_tarkov()
    seed_other()
    start_server()
