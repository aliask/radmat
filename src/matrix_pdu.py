#!/usr/bin/env python3

import struct
from PIL import Image


class FramePDU:
    IDENT = 0x1234
    height = 0
    width = 0
    pixeldata = b""

    def from_image(self, image):
        img = Image.open(image).convert("RGB")
        img.load()
        self.height = img.height
        self.width = img.width
        for y in range(img.height):
            for x in range(img.width):
                (r, g, b) = img.getpixel((x, img.height - y - 1))
                a = 255
                self.pixeldata += struct.pack("BBBB", r, g, b, a)

    def as_binary(self):
        header = struct.pack(
            "HHHH", self.IDENT, self.height, self.width, len(self.pixeldata)
        )
        return header + self.pixeldata


class CommandPDU:
    IDENT = 0x4321
    CMD_BRIGHTNESS = 0

    def __init__(self, command, value):
        self.command = command
        self.value = value

    def as_binary(self):
        return struct.pack("HBB", self.IDENT, self.command, self.value)
