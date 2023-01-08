#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from enum import Enum
import logging
import socket
import struct

from PIL import Image


class NetworkPDU(object, metaclass=ABCMeta):
    IDENT = 0x0000

    @abstractmethod
    def as_binary(self) -> bytes:
        pass


class FramePDU(NetworkPDU):
    pixels: bytes
    height: int
    width: int
    IDENT = 0x1234

    def __init__(self, height: int, width: int, pixels: bytes):
        self.height = height
        self.width = width
        self.pixels = pixels

    @classmethod
    def from_image(cls, image: Image.Image):
        img = image.convert("RGB")
        img.load()
        pixels = b""
        for y in range(img.height):
            for x in range(img.width):
                (r, g, b) = img.getpixel((x, img.height - y - 1))
                a = 255
                pixels += struct.pack("BBBB", r, g, b, a)
        return cls(height=img.height, width=img.width, pixels=pixels)

    def as_binary(self):
        header = struct.pack(
            "HHHH", self.IDENT, self.height, self.width, len(self.pixels)
        )
        return header + self.pixels


class Command(Enum):
    SetBrightness = 0
    SetPriority = 1


class CommandPDU(NetworkPDU):
    command: Command
    value: int
    IDENT = 0x4321

    def __init__(self, command, value):
        self.command = command
        self.value = value

    def as_binary(self):
        return struct.pack("HBB", self.IDENT, self.command.value, self.value)


def send_pdu(frame: NetworkPDU, destination: tuple):
    pdu_bytes = frame.as_binary()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(destination)
        s.sendall(pdu_bytes)


def test_connection(destination: tuple) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(destination)
        except OSError as e:
            logging.info(f"Connection failed: {e}")
            return False
    logging.info("Connected!")
    return True
    