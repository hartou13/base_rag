import socket
import os
from dotenv import load_dotenv

load_dotenv()
ip_address = None

def set_ip_address():
    global ip_address
    host_name = os.environ.get("MYSQL_HOST")
    try:
        ip_address = socket.gethostbyname(host_name)
        print(f"MySQL IP address: {ip_address}")
    except socket.gaierror:
        print(f"Unable to resolve host: {host_name}")