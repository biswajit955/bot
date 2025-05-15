#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess


def check_and_kill_port(port):
    """
    Check if a port is in use and kill the process using that port if it is.
    """
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        pid = result.stdout.strip()
        if pid:
            print(f"Port {port} is already in use by process {pid}. Killing the process...")
            os.system(f'kill -9 {pid}')
    except Exception as e:
        print(f"Error checking and killing port: {e}")

def main():
    port = 8000
    check_and_kill_port(port)
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
