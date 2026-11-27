r"""arcade_compare: a frame of ours beside the art direction target and, optionally, a stock frame of the same kind of place; same height,
names burned in.

    python arcade_compare.py <frame.png> <out.jpg> [target] [stock frame]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

TARGET = r'C:\studio-data\sz\film\concept\arcade.png'


def label_of(p, kind):
    parts = p.replace('\\', '/').split('/')
    return '%s %s' % (kind, '/'.join(parts[-2:]))


def main():
    frame, out = sys.argv[1], sys.argv[2]
    target = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else TARGET
    stock = sys.argv[4] if len(sys.argv) > 4 else None
    h = 540
    panels = [(target, 'TARGET'), (frame, 'GAME')] + ([(stock, 'STOCK')] if stock else [])
    ims = []
    for p, kind in panels:
        im = Image.open(p).convert('RGB')
        im = im.resize((int(im.width * h / im.height), h))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 30], fill=(0, 0, 0))
        d.text((8, 4), label_of(p, kind), fill=(255, 230, 0), font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 22))
        ims.append(im)
    s = Image.new('RGB', (sum(i.width for i in ims), h))
    x = 0
    for i in ims:
        s.paste(i, (x, 0))
        x += i.width
    s.save(out, quality=90)
    print(out)


if __name__ == '__main__':
    main()
