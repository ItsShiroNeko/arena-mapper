"""Drawing sinks: a common interface over a Tk canvas and an SVG document."""
from xml.sax.saxutils import escape as xml_escape

from ..theme import F


class TkSink:
    def __init__(self, canvas, tag="scene"):
        self.c, self.tag = canvas, tag

    def polygon(self, pts, fill="", outline="", width=1, dash=None):
        flat = [v for p in pts for v in p]
        self.c.create_polygon(*flat, fill=fill, outline=outline, width=width, dash=dash, tags=self.tag)

    def line(self, pts, fill="#000", width=1, dash=None, cap="butt"):
        flat = [v for p in pts for v in p]
        self.c.create_line(*flat, fill=fill, width=width, dash=dash, capstyle=cap, tags=self.tag)

    def oval(self, cx, cy, r, fill="", outline="", width=1, dash=None):
        self.c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=outline, width=width,
                           dash=dash, tags=self.tag)

    def text(self, x, y, s, size=9, fill="#fff", anchor="center", bold=False):
        self.c.create_text(x, y, text=s, fill=fill, anchor=anchor, font=F(size, bold), tags=self.tag)


class SvgSink:
    def __init__(self, w, h, bg):
        self.w, self.h, self.bg, self.items = w, h, bg, []

    @staticmethod
    def _c(c):
        return c if c else "none"

    @staticmethod
    def _d(dash):
        return f' stroke-dasharray="{dash[0]},{dash[1]}"' if dash else ""

    def polygon(self, pts, fill="", outline="", width=1, dash=None):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.items.append(f'<polygon points="{p}" fill="{self._c(fill)}" stroke="{self._c(outline)}" '
                          f'stroke-width="{width}"{self._d(dash)}/>')

    def line(self, pts, fill="#000", width=1, dash=None, cap="butt"):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.items.append(f'<polyline points="{p}" fill="none" stroke="{fill}" stroke-width="{width}" '
                          f'stroke-linecap="{cap}"{self._d(dash)}/>')

    def oval(self, cx, cy, r, fill="", outline="", width=1, dash=None):
        self.items.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{self._c(fill)}" '
                          f'stroke="{self._c(outline)}" stroke-width="{width}"{self._d(dash)}/>')

    def text(self, x, y, s, size=9, fill="#000", anchor="center", bold=False):
        ta = "end" if "e" in anchor and anchor != "center" else "start" if "w" in anchor else "middle"
        if anchor == "center":
            y += size * 0.35
        elif "n" in anchor:
            y += size * 0.9
        wt = ' font-weight="bold"' if bold else ""
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size + 2}" fill="{fill}" '
                          f'text-anchor="{ta}" font-family="Helvetica, Arial, sans-serif"{wt}>'
                          f'{xml_escape(s)}</text>')

    def render(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" '
                f'viewBox="0 0 {self.w:.0f} {self.h:.0f}">')
        bg = f'<rect width="100%" height="100%" fill="{self.bg}"/>'
        return "\n".join([head, bg] + self.items + ["</svg>"])
