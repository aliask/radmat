#!/usr/bin/env python3

import ftplib
import logging
import os
import glob
from PIL import Image
import time
from matrix_pdu import FramePDU, CommandPDU
import socket
import schedule

RADAR_ID = os.environ.get("RADAR_ID", "IDR023")
LEDSERVER_PORT = int(os.environ.get("LEDSERVER_PORT", 20304))

DESTINATION_PANEL = ("127.0.0.1", LEDSERVER_PORT)
PANEL_SIZE = (32, 16)

# Avoid re-downloading every time
FILES_TO_CACHE = 30

download_root = "/tmp/radar/download/"
ready_root = "/tmp/radar/ready/"

logging.getLogger().setLevel(logging.INFO)


def fetch_new_images(radar_id, outdir):
    try:
        fc = ftplib.FTP("ftp.bom.gov.au")
        fc.login()
        fc.cwd("/anon/gen/radar")
    except Exception as e:
        logging.exception(e)
        return

    remote_files = fc.nlst()
    for file in remote_files:
        logging.debug("FTP file: " + file)
        local_file = os.path.join(outdir, file)
        if file.startswith(radar_id + ".T.") and not os.path.exists(local_file):
            logging.info("Downloading " + file)
            with open(local_file, "wb") as fh:
                fc.retrbinary("RETR " + file, fh.write)

    fc.close()


def resize_image(infile, outfile):
    im = Image.open(infile)
    ow, oh = im.size
    outim = im.crop(box=(0, oh * 0.25, ow, oh * 0.75))
    outim = outim.resize(size=PANEL_SIZE, resample=Image.BILINEAR)
    outim.save(outfile)


def resize_all_images(directory, outdir):
    downloaded_files = os.listdir(directory)
    for file in downloaded_files:
        infile = os.path.join(directory, file)
        outfile = os.path.join(outdir, file)
        if not os.path.exists(outfile):
            logging.debug("Resizing " + file)
            resize_image(infile, outfile)


def send_image(file, opened_socket):
    logging.debug("Sending " + file)
    frame = FramePDU()
    frame.from_image(file)
    pdu_bytes = frame.as_binary()
    ret = opened_socket.sendto(pdu_bytes, DESTINATION_PANEL)


def send_images(files, delay):
    opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for file in files:
        send_image(file, opened_socket=opened_socket)
        time.sleep(delay)


def update_files():
    logging.info("Fetching new images from BOM")
    fetch_new_images(RADAR_ID, download_root)

    logging.info("Resizing images...")
    resize_all_images(download_root, ready_root)

    logging.info("Cleaning up old images...")
    all_files = sorted(glob.glob(download_root + "/*.png"))
    for stale_file in all_files[0:-FILES_TO_CACHE]:
        file = os.path.basename(stale_file)
        logging.info("Deleting " + file)
        os.unlink(stale_file)
        os.unlink(os.path.join(ready_root, file))

    logging.info("Done. Sending images to LEDServer")


def send_brightness(brightness: int):
    logging.debug("Setting brightness to " + str(brightness))
    cmd = CommandPDU(CommandPDU.CMD_BRIGHTNESS, brightness)
    pdu_bytes = cmd.as_binary()

    opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    opened_socket.sendto(pdu_bytes, DESTINATION_PANEL)


def main():
    os.makedirs(download_root, exist_ok=True)
    os.makedirs(ready_root, exist_ok=True)
    schedule.every(5).minutes.do(update_files)
    schedule.every(5).minutes.do(send_brightness, 20)
    update_files()

    while True:
        schedule.run_pending()
        dir_files = sorted(glob.glob(ready_root + "/*.png"))
        send_images(dir_files[-6:], delay=0.2)
        time.sleep(1)


if __name__ == "__main__":
    main()
