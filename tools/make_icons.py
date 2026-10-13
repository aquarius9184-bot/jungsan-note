"""앱 아이콘 PNG 생성 (외부 라이브러리 없이 표준 라이브러리만 사용).

파란 그라데이션 배경 + 흰색 '%' 기호.
실행: python tools/make_icons.py  → icons/ 폴더에 PNG 생성
"""
import math
import os
import struct
import zlib

OUT = os.path.join(os.path.dirname(__file__), "..", "icons")

TOP = (0x5B, 0x8C, 0xFF)     # 그라데이션 시작색
BOTTOM = (0x2F, 0x5B, 0xEA)  # 그라데이션 끝색
WHITE = (255, 255, 255)


def write_png(path, size, pixels):
    """pixels: size*size 개의 (r, g, b, a) 튜플"""
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter: none
        for x in range(size):
            raw.extend(pixels[y * size + x])

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---- 거리 함수(SDF): 음수면 도형 안쪽 ----
def sd_circle(px, py, cx, cy, r):
    return math.hypot(px - cx, py - cy) - r


def sd_capsule(px, py, ax, ay, bx, by, r):
    pax, pay, bax, bay = px - ax, py - ay, bx - ax, by - ay
    h = max(0.0, min(1.0, (pax * bax + pay * bay) / (bax * bax + bay * bay)))
    return math.hypot(pax - bax * h, pay - bay * h) - r


def sd_round_rect(px, py, half, radius):
    qx = abs(px - 0.5) - half + radius
    qy = abs(py - 0.5) - half + radius
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius


def render(size, rounded, glyph_scale):
    px_unit = 1.0 / size
    pixels = []
    for y in range(size):
        for x in range(size):
            u, v = (x + 0.5) / size, (y + 0.5) / size

            # 배경
            if rounded:
                d_bg = sd_round_rect(u, v, 0.5, 0.22)
                a_bg = max(0.0, min(1.0, 0.5 - d_bg / px_unit))
            else:
                a_bg = 1.0
            t = (u + v) / 2
            bg = tuple(TOP[i] + (BOTTOM[i] - TOP[i]) * t for i in range(3))

            # '%' 기호 (중앙 기준으로 glyph_scale 만큼 축소)
            gu = 0.5 + (u - 0.5) / glyph_scale
            gv = 0.5 + (v - 0.5) / glyph_scale
            d = min(
                sd_circle(gu, gv, 0.335, 0.335, 0.095),
                sd_circle(gu, gv, 0.665, 0.665, 0.095),
                sd_capsule(gu, gv, 0.69, 0.27, 0.31, 0.73, 0.045),
            )
            a_g = max(0.0, min(1.0, 0.5 - d / (px_unit / glyph_scale)))

            rgb = tuple(round(bg[i] * (1 - a_g) + WHITE[i] * a_g) for i in range(3))
            pixels.append((*rgb, round(a_bg * 255)))
    return pixels


def main():
    os.makedirs(OUT, exist_ok=True)
    targets = [
        # 파일명, 크기, 모서리 둥글게, 기호 크기
        ("icon-192.png", 192, True, 0.82),
        ("icon-512.png", 512, True, 0.82),
        # maskable: 기기마다 원/둥근사각형으로 잘라내므로 꽉 채우고 기호는 안전영역(80%) 안에
        ("icon-maskable-512.png", 512, False, 0.62),
        # iOS는 자체적으로 모서리를 둥글게 처리
        ("apple-touch-icon.png", 180, False, 0.75),
    ]
    for name, size, rounded, scale in targets:
        write_png(os.path.join(OUT, name), size, render(size, rounded, scale))
        print("생성:", name)


if __name__ == "__main__":
    main()
