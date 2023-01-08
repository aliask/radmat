#!/usr/bin/env python3

import ftplib
import glob
import logging
import os
import threading
import time
from typing import List

from PIL import Image, UnidentifiedImageError
import schedule

from matrix_pdu import FramePDU, CommandPDU, Command, send_pdu, test_connection

RADAR_ID = os.environ.get("RADAR_ID", "IDR023")

LEDSERVER_PORT = int(os.environ.get("LEDSERVER_PORT", "20304"), base=10)
LEDSERVER_HOST = os.environ.get("LEDSERVER_HOST", "127.0.0.1")
DESTINATION_PANEL = (LEDSERVER_HOST, LEDSERVER_PORT)

LED_WIDTH = int(os.environ.get("LED_WIDTH", "32"), base=10)
LED_HEIGHT = int(os.environ.get("LED_HEIGHT", "16"), base=10)
LED_BRIGHTNESS = int(os.environ.get("LED_BRIGHTNESS", "20"), base=10)
PANEL_SIZE = (LED_WIDTH, LED_HEIGHT)

# Avoid re-downloading every time
FILES_TO_CACHE = 30

download_root = "/tmp/radar/download/"
ready_root = "/tmp/radar/ready/"

frame_cache_lock = threading.Lock()
frame_cache: List[FramePDU] = []

logging.basicConfig(
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def fetch_new_images(radar_id: str, outdir: str):
    try:
        with ftplib.FTP("ftp.bom.gov.au") as fc:
            fc.login()
            fc.cwd("/anon/gen/radar")

            remote_files = fc.nlst()
            for file in remote_files:
                logging.debug("FTP file: " + file)
                local_file = os.path.join(outdir, file)
                if file.startswith(radar_id + ".T.") and not os.path.exists(local_file):
                    logging.info("Downloading " + file)
                    try:
                        with open(local_file, "wb") as fh:
                            fc.retrbinary("RETR " + file, fh.write)
                    except ftplib.all_errors as e:
                        logging.error(f"Error while downloading {file} from FTP: {e}")
                        logging.debug("Debug trace", exc_info=e)

    except ftplib.all_errors as e:
        logging.error(f"Error while connecting to FTP server (ftp.bom.gov.au): {e}")
        logging.debug("Debug trace", exc_info=e)


def resize_image(infile: str, outfile: str):
    im = Image.open(infile)
    ow, oh = im.size
    outim = im.crop(box=(0, int(oh * 0.25, base=10), ow, int(oh * 0.75, base=10)))
    outim = outim.resize(size=PANEL_SIZE, resample=Image.BILINEAR)
    outim.save(outfile)


def resize_all_images(directory: str, outdir: str):
    downloaded_files = os.listdir(directory)
    for downloaded_file in downloaded_files:
        infile = os.path.join(directory, downloaded_file)
        outfile = os.path.join(outdir, downloaded_file)
        if not os.path.exists(outfile) and downloaded_file.endswith(".png"):
            logging.debug("Resizing " + downloaded_file)
            try:
                resize_image(infile, outfile)
            except UnidentifiedImageError as e:
                logging.warning(f"Unkown image format for file: {infile}", exc_info=e)
                os.unlink(infile)


def decode_images(files: List[str]):
    frames: List[FramePDU] = []
    for file in files:
        logging.debug("Decoding " + file)
        image = Image.open(file)
        frames.append(FramePDU.from_image(image))
    return frames


def send_frames(frames: List[FramePDU], delay: float):
    logging.debug("Sending Frames to LEDServer")
    for frame in frames:
        send_pdu(frame, DESTINATION_PANEL)
        time.sleep(delay)


def update_files():
    global frame_cache
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

    logging.info("Converting images to Frames for panel")
    dir_files = sorted(glob.glob(ready_root + "/*.png"))

    # Pre-decode the frames, then copy to minimise lock duration
    frames = decode_images(dir_files[-6:])
    with frame_cache_lock:
        frame_cache = frames.copy()

    logging.info(f"Done. Sending {len(frame_cache)} images to LEDServer")


def update_files_thread():
    job_thread = threading.Thread(target=update_files)
    job_thread.start()


def send_brightness(brightness: int):
    logging.info("Setting brightness to " + str(brightness))
    cmd = CommandPDU(Command.SetBrightness, brightness)
    send_pdu(cmd, DESTINATION_PANEL)


def main():
    logging.info("Starting BOM radar streaming service with following config:")
    logging.info(f"  - Radar ID: {RADAR_ID}")
    logging.info(f"  - Panel Dimensions: {LED_WIDTH}x{LED_HEIGHT}")
    logging.info(f"  - Brightness: {LED_BRIGHTNESS}")
    logging.info(f"  - LEDServer: tcp://{LEDSERVER_HOST}:{LEDSERVER_PORT}")

    # Prepare required folders
    os.makedirs(download_root, exist_ok=True)
    os.makedirs(ready_root, exist_ok=True)

    # Set up schedule for fetching new images
    schedule.every(5).minutes.do(update_files_thread)

    # Pre-fetch the files for first run
    update_files()

    # Attempt connection to panel and set brightness
    try:
        send_brightness(LED_BRIGHTNESS)
        panel_connected = True
    except OSError as e:
        logging.warning(f"Couldn't send to LEDServer: {e}")
        panel_connected = False

    # Main loop
    while True:
        try:
            if panel_connected:
                # Update files if it's time
                schedule.run_pending()

                # Create a copy of the frame cache in to minimise lock duration
                with frame_cache_lock:
                    frames = frame_cache.copy()

                # Send a cycle of the radar images
                send_frames(frames=frames, delay=0.2)

                # Pause between radar cycles
                time.sleep(1)
            else:
                time.sleep(60)
                logging.info(f"Retrying connection to LEDServer at tcp://{LEDSERVER_HOST}:{LEDSERVER_PORT}...")
                panel_connected = test_connection(DESTINATION_PANEL)
                if panel_connected:
                    send_brightness(LED_BRIGHTNESS)
        except OSError as e:
            panel_connected = False
            logging.warning(f"Couldn't send to LEDServer: {e}")


if __name__ == "__main__":
    main()
