import pytest
from PIL import Image, ImageDraw

BOXES = [(35, 42, 244, 296), (266, 42, 475, 296), (35, 318, 244, 572), (266, 318, 475, 572)]


@pytest.fixture
def scan_factory():
    def make(occupied=(0, 1, 2, 3), scale=1, shift=0):
        image = Image.new("RGB", (510, 702), (32, 32, 32))
        draw = ImageDraw.Draw(image)
        for index, (x0, y0, x1, y1) in enumerate(BOXES):
            y0, y1 = y0 + shift, y1 + shift
            if index in occupied:
                draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill="white")
                draw.rectangle((x0 + 14, y0 + 14, x1 - 14, y1 - 55), fill=(12, 12, 12))
                draw.line((x0 + 25, y1 - 30, x1 - 25, y1 - 25), fill="black", width=3)
            else:
                for cy in (y0 + 48, y1 - 40):
                    cx = (x0 + x1) // 2
                    draw.ellipse((cx - 25, cy - 25, cx + 25, cy + 25), fill="white")
        if scale != 1:
            image = image.resize((510 * scale, 702 * scale), Image.Resampling.NEAREST)
        return image

    return make
