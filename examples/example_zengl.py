import string
import struct
import sys

import pygame
import zengl
from font_atlas import load_font

pygame.init()

pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, 1)
pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

screen = pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)
ctx = zengl.context()


class Font:
    def __init__(self, framebuffer, viewport):
        self.ctx = zengl.context()

        fonts = [
            open("examples/Inconsolata-Regular.ttf", "rb").read(),
            open("examples/Inconsolata-Bold.ttf", "rb").read(),
        ]
        self.fonts = ["regular", "bold"]
        self.font_sizes = [16.0, 24.0, 32.0]
        code_points = [ord(x) for x in string.printable]

        texture_size = (512, 512)
        pixels, glyphs = load_font(texture_size, fonts, self.font_sizes, code_points)

        self.glyph_lookup = {x: i for i, x in enumerate(code_points)}
        self.glyph_struct = struct.Struct("Q3f")
        self.glyphs = glyphs

        self.texture = self.ctx.image(texture_size, "rgba8unorm", pixels)

        self.instance = struct.Struct("2fQ1I")
        self.instances = bytearray(self.instance.size * 100000)
        self.instance_buffer = self.ctx.buffer(self.instances)
        self.instance_count = 0

        self.pipeline = self.ctx.pipeline(
            vertex_shader="""
                #version 300 es
                precision highp float;

                uniform vec2 screen_size;
                uniform vec2 texture_size;

                vec2 vertices[4] = vec2[](
                    vec2(0.0, 0.0),
                    vec2(0.0, 1.0),
                    vec2(1.0, 0.0),
                    vec2(1.0, 1.0)
                );

                layout (location = 0) in vec2 in_position;
                layout (location = 1) in ivec4 in_bbox;
                layout (location = 2) in vec4 in_color;

                out vec2 v_texcoord;
                out vec4 v_color;

                void main() {
                    v_color = in_color;
                    v_texcoord = mix(vec2(in_bbox.xy), vec2(in_bbox.zw), vertices[gl_VertexID]) / texture_size;
                    vec2 vertex = in_position + vertices[gl_VertexID] * vec2(in_bbox.zw - in_bbox.xy);
                    gl_Position = vec4(vertex / screen_size * 2.0 - 1.0, 0.0, 1.0);
                    gl_Position.y *= -1.0;
                }
            """,
            fragment_shader="""
                #version 300 es
                precision highp float;

                in vec2 v_texcoord;
                in vec4 v_color;

                uniform sampler2D Texture;

                layout (location = 0) out vec4 out_color;

                void main() {
                    float alpha = texture(Texture, v_texcoord).r;
                    if (alpha < 0.001) {
                        discard;
                    }
                    out_color = vec4(v_color.rgb, v_color.a * alpha);
                }
            """,
            layout=[
                {
                    "name": "Texture",
                    "binding": 0,
                },
            ],
            resources=[
                {
                    "type": "sampler",
                    "binding": 0,
                    "image": self.texture,
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                },
            ],
            blend={
                "enable": True,
                "src_color": "src_alpha",
                "dst_color": "one_minus_src_alpha",
            },
            uniforms={
                "screen_size": viewport[2:],
                "texture_size": texture_size,
            },
            framebuffer=framebuffer,
            viewport=viewport,
            topology="triangle_strip",
            vertex_buffers=zengl.bind(self.instance_buffer, "2f 4i2 4nu1 /i", 0, 1, 2),
            vertex_count=4,
            instance_count=0,
        )

    def clear(self):
        self.instance_count = 0

    def text(self, x, y, text, font, size, color):
        col = int(color[5:7] + color[3:5] + color[1:3], 16) | 0xFF000000
        font_index = self.fonts.index(font)
        size_index = self.font_sizes.index(size)
        num_sizes = len(self.font_sizes)
        num_glyphs = len(self.glyph_lookup)
        cursor = x
        for c in text:
            glyph_index = self.glyph_lookup[ord(c)]
            idx = ((font_index * num_sizes + size_index) * num_glyphs + glyph_index) * 28
            bbox, xoff, yoff, xadvance = self.glyph_struct.unpack(self.glyphs[idx : idx + 20])
            at = self.instance_count * self.instance.size
            self.instance.pack_into(self.instances, at, cursor + xoff, y + yoff, bbox, col)
            self.instance_count += 1
            cursor += xadvance

    def render(self):
        instances_size = self.instance_count * self.instance.size
        self.instance_buffer.write(memoryview(self.instances)[:instances_size])
        self.pipeline.instance_count = self.instance_count
        self.pipeline.render()


font = Font(None, (0, 0, 800, 600))
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    font.clear()
    font.text(100.0, 100.0, "Hello World!", "regular", 16.0, "#ff0000")
    font.text(100.0, 130.0, "Hello World!", "bold", 16.0, "#ff0000")
    font.text(200.0, 100.0, "Hello World!", "regular", 24.0, "#00ff00")
    font.text(200.0, 130.0, "Hello World!", "bold", 24.0, "#00ff00")
    font.text(350.0, 100.0, "Hello World!", "regular", 32.0, "#0000ff")
    font.text(350.0, 130.0, "Hello World!", "bold", 32.0, "#0000ff")
    font.text(100.0, 160.0, string.printable, "regular", 16.0, "#ffffff")
    font.text(100.0, 320.0, f"fps: {clock.get_fps():.2f}", "bold", 16.0, "#ffffff")

    ctx.new_frame()
    font.render()
    ctx.end_frame()
    pygame.display.flip()
    clock.tick(60)
