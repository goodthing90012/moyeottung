# -*- coding: utf-8 -*-
"""모였텅 허브 아이콘/캐릭터 생성기.

입력  : assets-src/icon-source.png (배지형 앱 아이콘), assets-src/character-source.png (투명 캐릭터)
출력  : icon-192/512 (any), icon-maskable-192/512, apple-touch-icon(180), favicon.ico, character.png
"""
import sys, os
import numpy as np
from PIL import Image

SRC_DIR, OUT_DIR = sys.argv[1], sys.argv[2]
icon_src = Image.open(os.path.join(SRC_DIR, 'icon-source.png')).convert('RGBA')
char_src = Image.open(os.path.join(SRC_DIR, 'character-source.png')).convert('RGBA')


# ── 1. 아이콘 배지의 네 모서리 색으로 전면(full-bleed) 그라데이션을 만든다 ──────
def badge_corner_colors(im):
    b = np.array(im.convert('RGB')).astype(int)
    H, W, _ = b.shape
    diff = np.abs(b - b[0, 0]).sum(axis=2)
    ys, xs = np.nonzero(diff > 18)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    inset = int((x1 - x0) * 0.13)
    p = lambda cx, cy, r=26: b[cy - r:cy + r, cx - r:cx + r].reshape(-1, 3).mean(axis=0)
    return ((x0, y0, x1, y1),
            (p(x0 + inset, y0 + inset), p(x1 - inset, y0 + inset),
             p(x0 + inset, y1 - inset), p(x1 - inset, y1 - inset)))


BADGE_BOX, (TL, TR, BL, BR) = badge_corner_colors(icon_src)


def gradient(size):
    """네 모서리 색을 쌍선형 보간해 배지의 파스텔 그라데이션을 전면으로 확장."""
    u = np.linspace(0, 1, size)[None, :, None]
    v = np.linspace(0, 1, size)[:, None, None]
    top = TL * (1 - u) + TR * u
    bot = BL * (1 - u) + BR * u
    rgb = top * (1 - v) + bot * v
    out = np.zeros((size, size, 4), np.uint8)
    out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[:, :, 3] = 255
    return Image.fromarray(out, 'RGBA')


# ── 2. 캐릭터의 불투명 영역 bbox와 '안전원 반지름' 계산 ──────────────────────
a = np.array(char_src)
mask = a[:, :, 3] > 8
ys, xs = np.nonzero(mask)
CH_BOX = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
cw, chh = CH_BOX[2] - CH_BOX[0], CH_BOX[3] - CH_BOX[1]
cx, cy = (CH_BOX[0] + CH_BOX[2]) / 2, (CH_BOX[1] + CH_BOX[3]) / 2
side = max(cw, chh)
# bbox 폭으로 정규화한 각 불투명 픽셀의 중심거리 → 99.5%가 들어가는 반지름
r = np.hypot(xs - cx, ys - cy) / side
R995 = float(np.percentile(r, 99.5))
# maskable 안전영역: 한 변의 80% 지름 원 = 반지름 0.4
MASKABLE_SCALE = 0.40 / R995
print('캐릭터 bbox %dx%d, 정규화 반지름(99.5%%) %.3f' % (cw, chh, R995))
print('→ maskable 안전영역에 들어가는 최대 배율: 한 변의 %.1f%%' % (MASKABLE_SCALE * 100))


def char_square(pad_ratio=0.0):
    """캐릭터를 bbox 기준 정사각형으로 잘라낸다 (pad_ratio만큼 여백 추가)."""
    pad = int(side * pad_ratio)
    half = side / 2 + pad
    box = (int(round(cx - half)), int(round(cy - half)),
           int(round(cx + half)), int(round(cy + half)))
    out = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    src_box = (max(box[0], 0), max(box[1], 0), min(box[2], a.shape[1]), min(box[3], a.shape[0]))
    out.paste(char_src.crop(src_box), (src_box[0] - box[0], src_box[1] - box[1]))
    return out


CHAR_SQ = char_square()


def full_bleed(size, content_ratio):
    """전면 그라데이션 위에 캐릭터를 content_ratio(한 변 대비) 크기로 올린다."""
    bg = gradient(size)
    d = max(1, int(round(size * content_ratio)))
    ch = CHAR_SQ.resize((d, d), Image.LANCZOS)
    off = (size - d) // 2
    bg.alpha_composite(ch, (off, off))
    return bg


def save(im, name, **kw):
    p = os.path.join(OUT_DIR, name)
    im.save(p, **kw)
    print('  %-26s %5dx%-5d %7d bytes' % (name, im.size[0], im.size[1], os.path.getsize(p)))


print('\n생성:')
# any — 원본 배지를 그대로 (디자인된 앱 아이콘 모양 유지)
for s in (192, 512):
    save(icon_src.resize((s, s), Image.LANCZOS), 'icon-%d.png' % s, optimize=True)

# maskable — 전면 그라데이션 + 안전영역 안에 들어가는 캐릭터
for s in (192, 512):
    save(full_bleed(s, MASKABLE_SCALE), 'icon-maskable-%d.png' % s, optimize=True)

# apple-touch-icon — iOS는 투명을 검게 깔고 자체 마스크를 씌우므로 여백 없는 전면 버전.
# iOS 마스크는 원이 아니라 모서리가 둥근 사각형이라 안전영역이 더 넓다.
save(full_bleed(180, min(0.74, MASKABLE_SCALE * 1.3)).convert('RGB'), 'apple-touch-icon.png', optimize=True)

# favicon — 16px에서도 형태가 남도록 바깥 여백을 잘라낸 배지
badge = icon_src.crop(BADGE_BOX).convert('RGB')
ico_path = os.path.join(OUT_DIR, 'favicon.ico')
badge.resize((64, 64), Image.LANCZOS).save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print('  %-26s %s %7d bytes' % ('favicon.ico', '16/32/48/64', os.path.getsize(ico_path)))

# 캐릭터 — 허브 상단 로고용. 표시 84px의 2배(168px), 가장자리 잘림 방지용 여백 2%
save(char_square(0.02).resize((168, 168), Image.LANCZOS), 'character.png', optimize=True)
