#!/usr/bin/env python3
"""News-image entry: a classic newspaper front page for 22 November 2026.

Draws everything with pure Python (standard library only): a small
zlib-based PNG writer and a hand-made 5x7 bitmap font. No network, no
fonts from disk, no randomness, no time dependence -- the program writes
byte-identical output on every run.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------

WIDTH = 1024
HEIGHT = 1024

PAPER = (246, 241, 227)   # newsprint cream
INK = (20, 20, 20)        # near-black
RED = (166, 30, 30)       # headline accent red
NAVY = (29, 58, 95)       # dateline / rule accent
GREY = (107, 101, 88)     # small print grey
LIGHT = (232, 226, 208)   # light panel fill


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg[0] for _ in range(w * h))
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[i * 3] = bg[0]
            self.px[i * 3 + 1] = bg[1]
            self.px[i * 3 + 2] = bg[2]

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        for t in range(thick):
            for xx in range(x, x + w):
                self.set(xx, y + t, color)

    def vline(self, x, y, h, color, thick=1):
        for t in range(thick):
            for yy in range(y, y + h):
                self.set(x + t, yy, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for t in range(thick):
                self.set(x + t, y, color)
                self.set(x, y + t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, thick=1):
        # Midpoint circle outline.
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                for t in range(thick):
                    self.set(px + t, py, color)
                    self.set(px, py + t, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def ellipse_points(self, cx, cy, rx, ry, color):
        # Parametric ellipse outline, deterministic step.
        import math
        steps = 120
        for i in range(steps + 1):
            a = 2.0 * math.pi * i / steps
            x = int(round(cx + rx * math.cos(a)))
            y = int(round(cy + ry * math.sin(a)))
            self.set(x, y, color)


# ---------------------------------------------------------------------------
# 5x7 bitmap font (hand-made). '#' = ink, '.' = empty.
# ---------------------------------------------------------------------------

FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}


def text_width(text, scale):
    """Pixel width of text at the given integer scale."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, color):
    """Draw one line of text, top-left at (x, y)."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, cx, y, text, scale, color):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap_lines(text, max_width, scale):
    """Greedy word wrap into lines that fit max_width pixels."""
    words = text.split(' ')
    lines = []
    cur = ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_paragraph(cv, x, y, text, max_width, scale, color, line_h=None):
    if line_h is None:
        line_h = 7 * scale + 4
    for line in wrap_lines(text, max_width, scale):
        draw_text(cv, x, y, line, scale, color)
        y += line_h
    return y


# ---------------------------------------------------------------------------
# Small drawn illustrations
# ---------------------------------------------------------------------------

def draw_globe(cv, cx, cy, r, color):
    """A cracked globe: circle, meridians, equator, a zig-zag crack."""
    cv.circle(cx, cy, r, color, thick=3)
    cv.ellipse_points(cx, cy, r, r // 2, color)
    cv.ellipse_points(cx, cy, r // 2, r, color)
    cv.hline(cx - r, cy, 2 * r, color, thick=2)
    cv.vline(cx, cy - r, 2 * r, color, thick=2)
    # Crack across the globe.
    cv.line(cx - r // 2, cy - r // 3, cx - r // 6, cy, RED, thick=3)
    cv.line(cx - r // 6, cy, cx + r // 6, cy - r // 4, RED, thick=3)
    cv.line(cx + r // 6, cy - r // 4, cx + r // 2, cy + r // 3, RED, thick=3)


def draw_capitol(cv, x, y, w, h, color):
    """A small capitol dome: dome arc, drum, base, columns."""
    import math
    dome_r = w // 3
    cx = x + w // 2
    base_y = y + h - 6
    # Dome: upper half circle.
    steps = 40
    for i in range(steps + 1):
        a = math.pi * i / steps
        px = int(round(cx + dome_r * math.cos(a)))
        py = int(round(y + 26 - dome_r * math.sin(a)))
        cv.fill_rect(px, py, 3, 3, color)
    # Flag pole and flag.
    cv.vline(cx, y - 6, 12, color, thick=2)
    cv.fill_rect(cx + 2, y - 6, 12, 7, RED)
    # Drum and base.
    cv.fill_rect(cx - dome_r, y + 26, 2 * dome_r, 8, color)
    cv.fill_rect(x + 6, base_y - 26, w - 12, 26, color)
    # Columns.
    for i in range(5):
        col_x = x + 12 + i * ((w - 24) // 4)
        cv.vline(col_x, base_y - 24, 22, PAPER, thick=3)
    cv.hline(x, base_y, w, color, thick=3)


def draw_tanker(cv, x, y, w, h, color):
    """A supertanker with smoke and flame above it."""
    hull_y = y + h - 26
    # Hull.
    cv.fill_rect(x, hull_y, w, 20, color)
    cv.line(x, hull_y, x + 14, hull_y + 20, color, thick=2)
    cv.line(x + w, hull_y, x + w - 14, hull_y + 20, color, thick=2)
    # Deck cabins and stack.
    cv.fill_rect(x + w - 34, hull_y - 22, 24, 22, color)
    cv.fill_rect(x + 18, hull_y - 12, 30, 12, color)
    cv.fill_rect(x + 52, hull_y - 12, 30, 12, color)
    # Flames above the stack.
    fx = x + w - 26
    fy = hull_y - 22
    cv.line(fx - 8, fy, fx, fy - 16, RED, thick=3)
    cv.line(fx, fy - 16, fx + 8, fy, RED, thick=3)
    cv.line(fx - 4, fy, fx + 2, fy - 10, RED, thick=2)
    # Smoke puffs.
    cv.circle(fx - 2, fy - 24, 6, GREY, thick=2)
    cv.circle(fx + 8, fy - 32, 5, GREY, thick=2)
    # Waves.
    for i in range(4):
        wx = x + 6 + i * (w // 4)
        cv.line(wx, hull_y + 24, wx + 12, hull_y + 24, NAVY, thick=2)
        cv.line(wx + 16, hull_y + 24, wx + 24, hull_y + 24, NAVY, thick=2)


def draw_ship(cv, x, y, w, h, color):
    """A small warship silhouette with a blast star above it."""
    hull_y = y + h - 14
    cv.fill_rect(x + 4, hull_y, w - 8, 10, color)
    cv.line(x + 4, hull_y, x + 12, hull_y + 10, color, thick=2)
    cv.vline(x + w // 2, hull_y - 16, 16, color, thick=2)
    cv.fill_rect(x + w // 2 - 10, hull_y - 12, 20, 6, color)
    # Blast star.
    bx = x + w // 2
    by = y + 10
    for dx, dy in ((0, -8), (0, 8), (-8, 0), (8, 0),
                   (-6, -6), (6, -6), (-6, 6), (6, 6)):
        cv.line(bx, by, bx + dx, by + dy, RED, thick=2)


def draw_building(cv, x, y, w, h, color):
    """A small blocky building (UN offices) with a crack."""
    cv.fill_rect(x, y, w, h, color)
    for row in range(3):
        for col in range(4):
            wx = x + 6 + col * ((w - 12) // 4)
            wy = y + 6 + row * ((h - 12) // 3)
            cv.fill_rect(wx, wy, 7, 7, PAPER)
    cv.line(x + w // 2, y, x + w // 2 - 6, y + h // 2, RED, thick=2)
    cv.line(x + w // 2 - 6, y + h // 2, x + w // 2 + 4, y + h, RED, thick=2)


def draw_star_badge(cv, cx, cy, r, color):
    """A five-point star badge."""
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r // 2
        pts.append((int(round(cx + rad * math.cos(ang))),
                    int(round(cy + rad * math.sin(ang)))))
    for i in range(10):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % 10]
        cv.line(x0, y0, x1, y1, color, thick=2)


# ---------------------------------------------------------------------------
# PNG writer (zlib, deterministic)
# ---------------------------------------------------------------------------

def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        start = y * cv.w * 3
        raw.extend(cv.px[start:start + cv.w * 3])
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack('>I', len(data)) + kind + data
        out += struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


# ---------------------------------------------------------------------------
# The front page
# ---------------------------------------------------------------------------

def draw_page(cv):
    # Double border.
    cv.fill_rect(0, 0, WIDTH, HEIGHT, PAPER)
    cv.hline(10, 10, WIDTH - 20, INK, thick=3)
    cv.hline(10, HEIGHT - 13, WIDTH - 20, INK, thick=3)
    cv.vline(10, 10, HEIGHT - 20, INK, thick=3)
    cv.vline(WIDTH - 13, 10, HEIGHT - 20, INK, thick=3)
    cv.hline(20, 20, WIDTH - 40, INK, thick=1)
    cv.hline(20, HEIGHT - 21, WIDTH - 40, INK, thick=1)
    cv.vline(20, 20, HEIGHT - 40, INK, thick=1)
    cv.vline(WIDTH - 21, 20, HEIGHT - 40, INK, thick=1)

    # Masthead.
    draw_text_centered(cv, WIDTH // 2, 34, "THE WORLD", 13, INK)
    cv.hline(28, 138, WIDTH - 56, INK, thick=3)
    cv.hline(28, 144, WIDTH - 56, INK, thick=1)

    # Dateline bar: the date big and unmistakable.
    draw_text(cv, 34, 158, "NO. 327", 2, GREY)
    draw_text_centered(cv, WIDTH // 2, 154, "SUNDAY, 22 NOVEMBER 2026", 4, RED)
    draw_text(cv, WIDTH - 34 - text_width("SUNDAY EDITION", 2), 158,
              "SUNDAY EDITION", 2, GREY)
    cv.hline(28, 196, WIDTH - 56, INK, thick=3)

    # ---- Lead story: COP31 collapse ----
    draw_text_centered(cv, WIDTH // 2, 214, "COP31 TALKS", 10, INK)
    draw_text_centered(cv, WIDTH // 2, 292, "COLLAPSE", 10, INK)
    draw_text_centered(cv, WIDTH // 2, 380,
                       "NO DEAL IN ANTALYA AS FOSSIL-FUEL ROW SINKS SUMMIT",
                       3, NAVY)
    cv.hline(28, 414, WIDTH - 56, INK, thick=1)

    # Globe illustration (left) + lead body text (right).
    draw_globe(cv, 190, 492, 58, NAVY)
    draw_text(cv, 292, 432, "CLIMATE SUMMIT ENDS IN FAILURE", 2, RED)
    y = 456
    y = draw_paragraph(
        cv, 292, y,
        "THE UN CLIMATE SUMMIT ENDED WITH NO DEAL ON SUNDAY. "
        "THE FINAL DRAFT OMITTED ANY MENTION OF FOSSIL FUELS.",
        700, 2, INK)
    y = draw_paragraph(
        cv, 292, y + 6,
        "THE EU, PANAMA, THE MARSHALL ISLANDS AND NORWAY "
        "REJECTED IT. THE LONGEST COP ON RECORD.",
        700, 2, INK)
    draw_text(cv, 292, y + 6, "GUTERRES: PROFOUND FRUSTRATION", 2, NAVY)
    cv.hline(28, 566, WIDTH - 56, INK, thick=3)

    # ---- Middle row: two columns ----
    # Left: Democrats win the House.
    draw_text(cv, 34, 584, "DEMOCRATS WIN", 5, INK)
    draw_text(cv, 34, 626, "THE HOUSE", 5, INK)
    draw_text(cv, 34, 672, "LARGEST MAJORITY SINCE 1992", 2, RED)
    draw_capitol(cv, 34, 700, 130, 84, NAVY)
    draw_paragraph(
        cv, 180, 700,
        "HUBBARD BEATS FOXX BY ABOUT 330 VOTES IN THE NC "
        "RECOUNT. DEMOCRATS HOLD 258 OF 435 SEATS.",
        316, 2, INK)
    # Divider.
    cv.vline(512, 584, 200, INK, thick=1)
    # Right: tankers hit by mines.
    draw_text(cv, 530, 584, "TANKERS HIT", 5, INK)
    draw_text(cv, 530, 626, "BY MINES", 5, INK)
    draw_text(cv, 530, 672, "TWO SUPERTANKERS ABLAZE", 2, RED)
    draw_tanker(cv, 530, 700, 150, 84, NAVY)
    draw_paragraph(
        cv, 696, 700,
        "IRAN'S NAVY SAID TWO SUPERTANKERS HIT NAVAL MINES "
        "AND CAUGHT FIRE EAST OF THE STRAIT OF HORMUZ.",
        296, 2, INK)
    cv.hline(28, 800, WIDTH - 56, INK, thick=3)

    # ---- Bottom strip: three small stories ----
    boxes = [
        (20, "UKRAINE", "DRONE HITS RUSSIAN WARSHIP",
         "MERKURY STRUCK OFF LIBYA", "ship"),
        (352, "SUDAN", "DRONES KILL FOUR",
         "UN BUILDING DAMAGED IN KHARTOUM", "building"),
        (684, "MEXICO", "EL CHAPO ISIDRO CAPTURED",
         "CARTEL BOSS SEIZED IN SINALOA", "star"),
    ]
    for bx, kicker, head, body, art in boxes:
        cv.fill_rect(bx, 816, 320, 158, LIGHT)
        cv.hline(bx, 816, 320, INK, thick=2)
        cv.hline(bx, 972, 320, INK, thick=2)
        cv.vline(bx, 816, 158, INK, thick=2)
        cv.vline(bx + 318, 816, 158, INK, thick=2)
        draw_text(cv, bx + 12, 828, kicker, 2, RED)
        yb = 852
        for line in wrap_lines(head, 296, 2):
            draw_text(cv, bx + 12, yb, line, 2, INK)
            yb += 18
        for line in wrap_lines(body, 296, 2):
            draw_text(cv, bx + 12, yb, line, 2, GREY)
            yb += 18
        if art == "ship":
            draw_ship(cv, bx + 220, 900, 84, 56, NAVY)
        elif art == "building":
            draw_building(cv, bx + 236, 906, 64, 52, NAVY)
        else:
            draw_star_badge(cv, bx + 272, 932, 22, NAVY)

    # Footer.
    draw_text_centered(cv, WIDTH // 2, 984,
                       "THE WORLD - SUNDAY, 22 NOVEMBER 2026 - PAGE 1",
                       2, GREY)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    draw_page(cv)
    write_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
