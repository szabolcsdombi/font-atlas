import string
import struct

from font_atlas import load_font
from PIL import Image

fonts = [
    open("examples/Inconsolata-Regular.ttf", "rb").read(),
    open("examples/Inconsolata-Bold.ttf", "rb").read(),
]
font_sizes = [16.0, 24.0, 32.0]
code_points = [ord(x) for x in string.ascii_letters]

texture_size = (512, 512)
pixels, glyphs = load_font(texture_size, fonts, font_sizes, code_points)

glyph_struct = struct.Struct("Q3f")

num_fonts = len(fonts)
num_sizes = len(font_sizes)
num_glyphs = len(code_points)

for font_index in range(num_fonts):
    for size_index in range(num_sizes):
        for glyph_index in range(num_glyphs):
            idx = ((font_index * num_sizes + size_index) * num_glyphs + glyph_index) * 28
            bbox, xoff, yoff, xadvance = glyph_struct.unpack(glyphs[idx : idx + 20])
            bbox = struct.unpack("4H", bbox.to_bytes(8, "little"))
            code_point = code_points[glyph_index]
            if code_point > 32:
                info = f"font[{font_index}] size: {font_sizes[size_index]} glyph: '{chr(code_point)}'"
                print(f"{info} | {bbox = } {xoff = :.3f} {yoff = :.3f} {xadvance = :.3f}")

img = Image.frombuffer("RGBA", texture_size, pixels)
img.show()
