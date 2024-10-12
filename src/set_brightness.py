#!/usr/local/bin/python3

# Activate the virtual environment inside Python to allow simple execution
import os

base_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
activate_this = os.path.join(base_dir, "venv/bin/activate_this.py")
exec(open(activate_this).read())

import logging
from matrix_pdu import CommandPDU
import socket
import sys

LEDSERVER_PORT = int(os.environ.get("LEDSERVER_PORT", 20304))
LEDSERVER_HOST = os.environ.get("LEDSERVER_HOST", "127.0.0.1")
logging.getLogger().setLevel(logging.INFO)


def send_brightness(brightness: int):
    logging.debug("Setting brightness to " + str(brightness))
    cmd = CommandPDU(CommandPDU.CMD_BRIGHTNESS, brightness)
    pdu_bytes = cmd.as_binary()

    opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ret = opened_socket.sendto(pdu_bytes, (LEDSERVER_HOST, LEDSERVER_PORT))
    if ret != len(pdu_bytes):
        logging.error("Failed to send brightness command")


def main():
    if len(sys.argv) == 2 and sys.argv[1].isnumeric():
        send_brightness(brightness=int(sys.argv[1]))
    else:
        sys.stderr.write("Usage: ./set_brightness.py <BRIGHTNESS>")
        exit(1)


if __name__ == "__main__":
    main()
