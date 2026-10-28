"""Generate deterministic, mirrored blockie identicons using Pillow."""

import base64
import ctypes
from io import BytesIO
import logging
import math
from random import random

from PIL import Image, ImageColor, ImageDraw

log = logging.getLogger("blockies")

DEFAULT_SIZE = 8
DEFAULT_SCALE = 4
DEFAULT_RANDSEED_LEN = 4


def zero_fill_right_shift(num, shift):
    return (num & 0xFFFFFFFF) >> shift


def int32(num):
    return ctypes.c_int32(num).value


class Context:
    def __init__(self, seed, randseed_len=DEFAULT_RANDSEED_LEN):
        if not isinstance(seed, str):
            raise TypeError("seed must be a string")
        if not isinstance(randseed_len, int) or randseed_len < 1:
            raise ValueError("randseed_len must be a positive integer")
        randseed = self.randseed = [0] * randseed_len
        for i, char in enumerate(seed):
            idx = i % randseed_len
            randseed[idx] = int32(randseed[idx] << 5) - randseed[idx] + ord(char)

    def rand(self):
        randseed = self.randseed
        t = int32(randseed[0] ^ (randseed[0] << 11))
        for i in range(len(randseed) - 1):
            randseed[i] = randseed[i + 1]
        idx = len(randseed) - 1
        randseed[idx] = (
            int32(randseed[idx]) ^ (int32(randseed[idx]) >> 19) ^ t ^ (t >> 8)
        )
        return zero_fill_right_shift(randseed[idx], 0) / (1 << 31)

    def create_color(self):
        h = math.floor(self.rand() * 360)
        s = self.rand() * 60 + 40
        lightness = sum(self.rand() for _ in range(4)) * 25
        hsl = "hsl({},{}%,{}%)".format(h, round(s), round(lightness))
        try:
            return ImageColor.getrgb(hsl)
        except ValueError:
            log.exception("produced invalid color: %s", hsl)
            return (0, 0, 0)

    def create_image_data(self, size):
        data_width = (size + 1) // 2
        mirror_width = size - data_width
        data = []
        for _ in range(size):
            row = [math.floor(self.rand() * 2.3) for _ in range(data_width)]
            row.extend(reversed(row[:mirror_width]))
            data.extend(row)
        return data


def create(
    seed=None,
    color=None,
    bgcolor=None,
    size=DEFAULT_SIZE,
    scale=DEFAULT_SCALE,
    spotcolor=None,
    format="PNG",
):
    """Return encoded image bytes; omitted or empty seeds use a random seed."""
    for name, value in (("size", size), ("scale", scale)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("{} must be a positive integer".format(name))

    seed = seed or hex(math.floor(random() * 10**16))
    ctx = Context(seed)
    color = color or ctx.create_color()
    if isinstance(color, str):
        color = ImageColor.getrgb(color)
    bgcolor = bgcolor or ctx.create_color()
    if isinstance(bgcolor, str):
        bgcolor = ImageColor.getrgb(bgcolor)
    spotcolor = spotcolor or ctx.create_color()
    if isinstance(spotcolor, str):
        spotcolor = ImageColor.getrgb(spotcolor)

    image_data = ctx.create_image_data(size)
    image = Image.new("RGB", (size * scale, size * scale), bgcolor)
    draw = ImageDraw.Draw(image)
    for i, val in enumerate(image_data):
        if val == 0:
            continue
        row, col = divmod(i, size)
        x, y = col * scale, row * scale
        draw.rectangle(
            (x, y, x + scale - 1, y + scale - 1),
            fill=color if val == 1 else spotcolor,
        )

    stream = BytesIO()
    image.save(stream, format=format, optimize=True)
    return stream.getvalue()


def png_to_data_uri(data):
    return "data:image/png;base64,{}".format(base64.b64encode(data).decode("ascii"))
