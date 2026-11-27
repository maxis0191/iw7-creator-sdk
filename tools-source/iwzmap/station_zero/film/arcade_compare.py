r"""arcade_compare: the entrance frame beside the art direction target, same height, names burned in.

    python arcade_compare.py <frame.png> <out.jpg> [target]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

TARGET = r'C:\studio-data\sz\film\concept\arcade.png'


def main():
    frame, out = sys.argv[1], sys.argv[2]
    target = sys.argv[3] if len(sys.argv) > 3 else TARGET
    h = 540
    ims = []
    for p, label in ((target, 'TARGET concept/arcade.png'), (frame, 'GAME ' + frame.replace('\\', '/').split('/')[-2] + '/' + frame.replace('\\', '/').split('/')[-1])):
        im = Image.open(p).convert('RGB')
        im = im.resize((int(im.width * h / im.height), h))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 30], fill=(0, 0, 0))
        d.text((8, 4), label, fill=(255, 230, 0), font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 22))
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
