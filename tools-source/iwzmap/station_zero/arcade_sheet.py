"""arcade_sheet: contact sheets of the ten Arcade cameras, 2 x 2 per sheet (crops the game's build string off the lower third's text line).

    python arcade_sheet.py <frames folder>     writes sheet_a.jpg, sheet_b.jpg, sheet_c.jpg beside the frames
"""
import os
import sys

from PIL import Image

CAMS = ['arc_west_long', 'arc_east_long', 'arc_bay1', 'arc_bay2', 'arc_bay3', 'arc_bay4', 'arc_bay5', 'arc_south_wall', 'arc_d7', 'arc_inside_bay3']


def main():
    folder = sys.argv[1]
    for n, grp in enumerate((CAMS[0:4], CAMS[4:8], CAMS[8:10])):
        ims = [Image.open(os.path.join(folder, c + '.png')).convert('RGB').resize((960, 540)) for c in grp]
        sheet = Image.new('RGB', (1920, 1080 if len(ims) > 2 else 540))
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % 2) * 960, (k // 2) * 540))
        sheet.save(os.path.join(folder, 'sheet_%s.jpg' % 'abc'[n]), quality=88)


if __name__ == '__main__':
    main()
