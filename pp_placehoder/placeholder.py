from .colors import COLORS
import pkg_resources
import random
from PIL import Image, ImageFont, ImageDraw


class PlaceholderPic(object):
    DEFAULT_FONT_FILE = pkg_resources.resource_filename(
        __name__, "Raleway-SemiBold.ttf"
    )

    DEFAULTS = {
        "size": 300,
        "foreground": "#ffffff",
        "background": None,
        "font_file": DEFAULT_FONT_FILE,
        "font_size": None,
    }

    @classmethod
    def random_color(self):
        return "#%06x" % random.randint(0, 0xFFFFFF)

    def __init__(self, text, **kwargs):
        self.text = text
        options = PlaceholderPic.DEFAULTS.copy()
        options.update(**kwargs)
        if options["background"] is None:
            options["background"] = random.choice(COLORS)
        if options["font_size"] is None:
            options["font_size"] = int(options["size"] / 2.5)
        for key, value in options.items():
            setattr(self, key, value)
        self._image = None

    @property
    def image(self):
        if self._image is None:
            self._image = Image.new(
                mode="RGB", size=(self.size, self.size), color=self.background
            )
            draw = ImageDraw.Draw(self._image)
            font = ImageFont.truetype(font=self.font_file, size=self.font_size)
            text_width, text_height = draw.textsize(self.text, font=font)
            draw.text(
                (
                    (self.size - text_width) / 2,
                    (self.size - text_height * 1.275) / 2,
                ),
                self.text,
                self.foreground,
                font=font,
            )
        return self._image
