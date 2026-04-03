"""
Generate sample images for cv-17 Visual Image Search Engine.
Run: pip install Pillow && python generate_samples.py
Output: 12 images — 9 index images (3 categories x 3) + 3 query images.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(__file__)


def make_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def save(img, name):
    img.save(os.path.join(OUT, name))
    print(f"  created: {name}")


def tshirt(color, label):
    img = Image.new("RGB", (300, 300), (245, 245, 245))
    d = ImageDraw.Draw(img)
    # body
    d.polygon([(60, 120), (240, 120), (260, 280), (40, 280)], fill=color)
    # collar
    d.polygon([(120, 120), (150, 80), (180, 120)], fill=(245, 245, 245))
    # sleeves
    d.polygon([(60, 120), (20, 160), (50, 180), (80, 140)], fill=color)
    d.polygon([(240, 120), (280, 160), (250, 180), (220, 140)], fill=color)
    d.text((100, 260), label, fill=(80, 80, 80), font=make_font(14))
    return img


def sneaker(color, sole, label):
    img = Image.new("RGB", (300, 200), (245, 245, 245))
    d = ImageDraw.Draw(img)
    d.ellipse([20, 120, 280, 175], fill=sole)
    d.polygon([(30, 130), (60, 70), (210, 60), (270, 120)], fill=color)
    d.ellipse([210, 85, 275, 140], fill=color)
    for lx in range(80, 200, 20):
        d.line([lx, 82, lx + 15, 96], fill=(255, 255, 255), width=2)
    d.text((90, 160), label, fill=(80, 80, 80), font=make_font(14))
    return img


def watch(face_color, band_color, label):
    img = Image.new("RGB", (300, 300), (245, 245, 245))
    d = ImageDraw.Draw(img)
    # band
    d.rectangle([125, 20, 175, 100], fill=band_color)
    d.rectangle([125, 200, 175, 280], fill=band_color)
    # case
    d.ellipse([70, 90, 230, 210], fill=(180, 180, 180))
    d.ellipse([80, 100, 220, 200], fill=face_color)
    # clock hands
    d.line([150, 150, 150, 115], fill=(255, 255, 255), width=3)
    d.line([150, 150, 175, 160], fill=(255, 255, 255), width=2)
    # hour markers
    for i in range(12):
        import math
        a = math.radians(i * 30 - 90)
        mx = 150 + int(55 * math.cos(a))
        my = 150 + int(55 * math.sin(a))
        d.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=(255, 255, 255))
    d.text((100, 265), label, fill=(80, 80, 80), font=make_font(14))
    return img


if __name__ == "__main__":
    print("Generating cv-17 samples...")
    # T-shirts (index)
    save(tshirt((60, 100, 200), "tshirt_blue"), "index_tshirt_blue.jpg")
    save(tshirt((200, 60, 60), "tshirt_red"), "index_tshirt_red.jpg")
    save(tshirt((60, 160, 80), "tshirt_green"), "index_tshirt_green.jpg")
    # Sneakers (index)
    save(sneaker((60, 60, 200), (40, 40, 40), "sneaker_blue"), "index_sneaker_blue.jpg")
    save(sneaker((200, 60, 60), (50, 50, 50), "sneaker_red"), "index_sneaker_red.jpg")
    save(sneaker((60, 60, 60), (30, 30, 30), "sneaker_black"), "index_sneaker_black.jpg")
    # Watches (index)
    save(watch((20, 20, 20), (40, 40, 40), "watch_black"), "index_watch_black.jpg")
    save(watch((180, 160, 100), (160, 130, 80), "watch_gold"), "index_watch_gold.jpg")
    save(watch((60, 100, 180), (50, 80, 160), "watch_blue"), "index_watch_blue.jpg")
    # Query images (slight variations)
    save(tshirt((70, 110, 210), "query_tshirt"), "query_tshirt.jpg")
    save(sneaker((70, 70, 210), (45, 45, 45), "query_sneaker"), "query_sneaker.jpg")
    save(watch((25, 25, 25), (45, 45, 45), "query_watch"), "query_watch.jpg")
    print("Done — 12 images in samples/")
