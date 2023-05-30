from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final, Iterable

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image

from resistor import ResistorValue, TolerancePercentColor

matplotlib.use("Agg")

E_12: Final[list[float]] = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
EXTRAS: Final[list[float]] = [3.0, 5.1]

CARD_WIDTH = 3.5
CARD_HEIGHT = 2


class ColorHex(str, Enum):
    """Manually chosen HTML color codes for good discrimination on paper"""

    black = "#000000"
    brown = "#8B4513"
    red = "#FF0000"
    orange = "#FFA500"
    yellow = "#FFFF00"
    green = "#008800"
    blue = "#00008B"
    violet = "#800080"
    gray = "#808080"
    grey = "#808080"
    white = "#FFFFFF"
    gold = "#FFD700"
    silver = "#C0C0C0"
    pink = "#FFC0CB"
    none = "#D2B48C"

    def __str__(self):
        return self.name


class ColorAbbr(str, Enum):
    """Abbreviations for colors"""

    black = "Bk"
    brown = "Br"
    red = "Rd"
    orange = "Or"
    yellow = "Yl"
    green = "Gr"
    blue = "Bl"
    violet = "Vt"
    gray = "Gy"
    grey = "Gy"
    white = "Wt"
    gold = "Gd"
    silver = "Sl"
    pink = "Pk"
    none = "x"

    def __str__(self):
        return self.value


@dataclass
class PolygonCoords:
    """x and y coordinates of a polygon"""

    x: list[float]
    y: list[float]


@dataclass(init=False)
class Square(PolygonCoords):
    """x and y coordinates of a square, created from a bottom-left coordinate and side length"""

    center_x: float
    center_y: float

    def __init__(self, x0: float, y0: float, side: float):
        self.x = [x0, x0 + side, x0 + side, x0]
        self.y = [y0, y0, y0 + side, y0 + side]
        self.center_x = x0 + side / 2
        self.center_y = y0 + side / 2


def gen_squares_coords(sq_side: float, spacing: float) -> tuple[list[Square], list[Square]]:
    """Generate coordinates for a set of four and and a set of five boxes on the business card

    Parameters
    ----------
    sq_side
        Length of the sides of each square
    spacing
        Spacing betwen squares

    Returns
    -------
    four_box_coords
        List of Square coordinate objects for the set of four squares
    five_box_coords
        List of Square coordinate objects for the set of five squares

    """
    # total width of four and five boxes
    four_box_width = sq_side * 4 + spacing * 3
    five_box_width = sq_side * 5 + spacing * 4

    # find a centered margin for each set of boxes
    four_box_x0 = (CARD_WIDTH - four_box_width) / 2
    five_box_x0 = (CARD_WIDTH - five_box_width) / 2

    five_box_y0 = five_box_x0  # even margins
    four_box_y0 = five_box_y0 + sq_side + spacing

    four_box_coords = [Square(four_box_x0 + i * (sq_side + spacing), four_box_y0, sq_side) for i in range(4)]

    five_box_coords = [Square(five_box_x0 + i * (sq_side + spacing), five_box_y0, sq_side) for i in range(5)]

    return four_box_coords, five_box_coords


def gen_border(ax: Axes, margin: float, linewidth: float = 1):
    """Generate a border around the business card at some margin in from the edge"""
    x = [margin, CARD_WIDTH - margin, CARD_WIDTH - margin, margin, margin]
    y = [margin, margin, CARD_HEIGHT - margin, CARD_HEIGHT - margin, margin]
    ax.plot(x, y, "-k", linewidth=linewidth)


def generate_card(
    rval: ResistorValue, four_box_tol: float = 5, five_box_tol: float = 1, figax: Figure | Axes | None = None
) -> tuple[Figure, Axes]:
    """Generate a business card for a certain value and tolerances for the four- and five- band version"""
    if isinstance(figax, Figure):
        fig = figax
        figax.clf()
        ax = figax.add_axes((0, 0, 1, 1))
    elif isinstance(figax, Axes):
        ax = figax
        fig = figax.figure
        ax.cla()
        ax.set_position([0, 0, 1, 1])
    else:
        fig, ax = plt.subplots()
        ax.set_position([0, 0, 1, 1])

    four_colors = [*rval.as_three_bands(), TolerancePercentColor(four_box_tol).name]
    five_colors = [*rval.as_four_bands(), TolerancePercentColor(five_box_tol).name]

    four_coords, five_coords = gen_squares_coords(sq_side=0.5, spacing=0.125)

    text_opts = {
        "horizontalalignment": "center",
        "verticalalignment": "center",
    }
    square_text_opts = text_opts | {"fontsize": "x-small", "bbox": {"facecolor": "#CCCCCC", "alpha": 0.5}}
    for color, square in zip(five_colors, five_coords):
        ax.fill(square.x, square.y, ColorHex[color])
        ax.text(square.center_x, square.center_y, ColorAbbr[color], **square_text_opts)

    for color, square in zip(four_colors, four_coords):
        ax.fill(square.x, square.y, ColorHex[color])
        ax.text(square.center_x, square.center_y, ColorAbbr[color], **square_text_opts)

    text_x = CARD_WIDTH / 2
    text_y = 1.7
    res_text_opts = text_opts | {"fontsize": "large", "fontweight": "bold"}
    ax.text(text_x, text_y, f"{rval}, {five_box_tol:g}%, {five_box_tol:g}%", **res_text_opts)
    gen_border(ax, 0.05)

    ax.axis("equal")
    ax.set_xlim(0, CARD_WIDTH)
    ax.set_ylim(0, CARD_HEIGHT)
    fig.set_figheight(CARD_HEIGHT)
    fig.set_figwidth(CARD_WIDTH)

    return fig, ax


def generate_cards(
    img_dir: Path,
    values: list[float],
    exponents: Iterable[int],
    four_box_tol: float = 5,
    five_box_tol: float = 1,
):
    """Generate and save a series of business card images for a given list of values and exponents (10*n).
    four_box_tol and five_box_tol specify the tolerance percent value to use for the four- and five-band
    color boxes, respectively.
    """
    rvalues = [ResistorValue.from_float(val * 10.0**exp) for exp in exponents for val in sorted(values)]
    fig = None
    for i, rval in enumerate(rvalues):
        fig, _ = generate_card(rval, four_box_tol, five_box_tol, fig)
        fig.savefig(str(img_dir / f"{i:03d}-{rval}.png"))


def gen_print_page(png_paths: list[Path], nrows, ncols, page_png_path: Path):
    """Generate a page of images from a series of images in row and columns. Expects that the images are all
    the same dimensions."""
    with Image.open(png_paths[0]) as sample_im:
        card_w = sample_im.width
        card_h = sample_im.height
    base_im = Image.new("RGB", (card_w * ncols, card_h * nrows), color=str(ColorHex["white"]))
    for i, png_path in enumerate(png_paths):
        with Image.open(png_path) as im:
            base_im.paste(im, box=((i % ncols) * card_w, (i // ncols) * card_h))
    base_im.save(page_png_path)


def gen_print_pages(png_dir: Path):
    """Generate pages of images of all the images in the png_dir"""
    # delete existing pages of pngs
    prefix = "page"
    for p in png_dir.glob("page*.png"):
        p.unlink()
    pngs = sorted(png_dir.glob("*.png"))
    for page_i, i in enumerate(range(0, len(pngs), 10)):
        page_png_path = png_dir / f"{prefix}_{page_i:02d}.png"
        gen_print_page(pngs[i : i + 10], 5, 2, page_png_path)


if __name__ == "__main__":
    png_dir = Path("pngs")
    extras = [3.0, 5.1]
    values = E_12 + extras
    png_dir.mkdir(exist_ok=True)
    generate_cards(png_dir, values=values, exponents=range(-1, 7))
    gen_print_pages(png_dir)
