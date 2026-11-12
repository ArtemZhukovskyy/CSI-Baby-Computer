"""Single-file MicroPython test for a 240x320 ST7789 SPI display.

Pico wiring: SCL=GP18, SDA=GP19, CS=GP17, DC=GP20, RST=GP21.
Display VCC and BL connect to 3V3(OUT); GND connects to GND.
Open in Thonny, save onto the Raspberry Pi Pico, and run.

The display initialization settings below are adapted from:
https://github.com/russhughes/st7789py_mpy

MIT License
Copyright (c) 2020-2023 Russ Hughes
Copyright (c) 2019 Ivan Belokobylskiy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from machine import Pin, SPI
from time import sleep_ms
import framebuf
import struct


# Change this message to your own short text (up to 13 characters).
MESSAGE = "HELLO PICO!"

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
YELLOW = 0xFFE0
CYAN = 0x07FF


class Display:
    # Landscape orientation for a physical 240x320 panel.
    width = 320
    height = 240

    def __init__(self):
        self.cs = Pin(17, Pin.OUT, value=1)
        self.dc = Pin(20, Pin.OUT, value=0)
        self.reset = Pin(21, Pin.OUT, value=1)
        self.spi = SPI(0, baudrate=10_000_000, polarity=0, phase=0,
                       sck=Pin(18), mosi=Pin(19))
        sleep_ms(10)
        self.reset.value(0)
        sleep_ms(20)
        self.reset.value(1)
        sleep_ms(150)
        self.command(0x01)  # Software reset.
        sleep_ms(150)
        settings = (
            (0x11, b"", 120),
            (0x13, b"", 0),
            (0xB6, b"\x0a\x82", 0),
            (0x3A, b"\x55", 10),
            (0xB2, b"\x0c\x0c\x00\x33\x33", 0),
            (0xB7, b"\x35", 0),
            (0xBB, b"\x28", 0),
            (0xC0, b"\x0c", 0),
            (0xC2, b"\x01\xff", 0),
            (0xC3, b"\x10", 0),
            (0xC4, b"\x20", 0),
            (0xC6, b"\x0f", 0),
            (0xD0, b"\xa4\xa1", 0),
            (0xE0, b"\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17", 0),
            (0xE1, b"\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e", 0),
            (0x21, b"", 0),
            (0x29, b"", 120),
        )
        for _ in range(2):
            for cmd, data, delay in settings:
                self.command(cmd, data)
                sleep_ms(delay)
        self.command(0x36, b"\x60")  # Landscape, RGB color order.

    def command(self, cmd, data=b""):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes((cmd,)))
        if data:
            self.dc.value(1)
            self.spi.write(data)
        self.cs.value(1)

    def window(self, x, y, width, height):
        if not (width > 0 and height > 0 and x >= 0 and y >= 0
                and x + width <= self.width and y + height <= self.height):
            raise ValueError("Drawing area must fit inside the display")
        self.command(0x2A, struct.pack(">HH", x, x + width - 1))
        self.command(0x2B, struct.pack(">HH", y, y + height - 1))
        self.command(0x2C)
        self.cs.value(0)
        self.dc.value(1)

    def fill_rect(self, x, y, width, height, color):
        pixel = struct.pack(">H", color)
        block = pixel * 256
        chunks, remainder = divmod(width * height, 256)
        self.window(x, y, width, height)
        try:
            for _ in range(chunks):
                self.spi.write(block)
            if remainder:
                self.spi.write(pixel * remainder)
        finally:
            self.cs.value(1)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def text(self, message, y, scale=2, color=WHITE, background=BLACK):
        # Render the built-in font a row at a time to keep memory use small.
        message = message[:self.width // (8 * scale)]
        if not message:
            return
        width = len(message) * 8
        bitmap = framebuf.FrameBuffer(bytearray(width), width, 8,
                                     framebuf.MONO_HLSB)
        bitmap.text(message, 0, 0, 1)
        row = bytearray(width * scale * 2)
        foreground_pixel = struct.pack(">H", color)
        background_pixel = struct.pack(">H", background)
        self.window((self.width - width * scale) // 2, y,
                    width * scale, 8 * scale)
        try:
            for source_y in range(8):
                position = 0
                for source_x in range(width):
                    pixel = (foreground_pixel if bitmap.pixel(source_x, source_y)
                             else background_pixel)
                    for _ in range(scale):
                        row[position] = pixel[0]
                        row[position + 1] = pixel[1]
                        position += 2
                for _ in range(scale):
                    self.spi.write(row)
        finally:
            self.cs.value(1)


def main():
    print("Starting ST7789 display test...")
    display = Display()
    for color in (RED, GREEN, BLUE):
        display.fill(color)
        sleep_ms(400)
    display.fill(BLACK)
    display.text(MESSAGE, 55, scale=3, color=CYAN)
    display.text("My first display", 105, scale=2)
    for index, color in enumerate((RED, YELLOW, GREEN, CYAN, BLUE)):
        display.fill_rect(20 + index * 56, 160, 56, 35, color)
    display.text("Made with Pico W", 215, scale=2, color=GREEN)
    print("Test sent. The message should remain on the display.")


if __name__ == "__main__":
    main()
