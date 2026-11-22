"""The route of a workout: the GPS track drawn to scale, north up, with
start and end and a scale bar. No map tiles: Pulsus loads no map data
(docs/decisions/route-without-map.md)."""
import math

from gi.repository import Adw, Gsk, Gtk, Pango

from pulsus.charts import ACCENT, ACCENT_DARK, _point, _rect, _rgba, _with_alpha
from pulsus.data import track

# A jump this long between two points is a lost signal, not a path: the
# line breaks there (gaps stay gaps).
GAP_METRES = 500.0
# Scale bar lengths to choose from, in metres.
SCALES = (50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000)
PADDING = 18


def project(points):
    """Flat x, y in metres (east, south) around the track's middle; good
    for the few kilometres of a workout."""
    lat0 = (min(p.lat for p in points) + max(p.lat for p in points)) / 2
    lon0 = (min(p.lon for p in points) + max(p.lon for p in points)) / 2
    k = math.pi / 180 * track.EARTH_RADIUS
    return [((p.lon - lon0) * k * math.cos(math.radians(lat0)), -(p.lat - lat0) * k)
            for p in points]


def scale_length(metres_wide):
    """The longest scale bar that takes at most a third of the width."""
    fitting = [s for s in SCALES if s <= metres_wide / 3]
    return fitting[-1] if fitting else SCALES[0]


def scale_text(metres):
    return f"{metres // 1000} km" if metres >= 1000 else f"{metres} m"


class Route(Gtk.Widget):
    __gtype_name__ = "PulsusRoute"

    def __init__(self, points, height=240):
        super().__init__(accessible_role=Gtk.AccessibleRole.IMG)
        self.height = height
        self.points = points
        self.flat = project(points)
        self.breaks = {n + 1 for n, (a, b) in enumerate(zip(points, points[1:]))
                       if track.metres(a, b) > GAP_METRES}
        apart = track.metres(points[0], points[-1])
        self.summary = (f"Route of about {track.length(points) / 1000:.1f} km, drawn "
                        f"to scale with north up. Start and end are "
                        f"{apart:.0f} m apart.")
        self.update_property([Gtk.AccessibleProperty.LABEL], [self.summary])

    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.VERTICAL:
            return self.height, self.height, -1, -1
        return 80, 320, -1, -1

    def _fit(self, width, height):
        """Metres -> pixels: (scale, x offset, y offset), track centred."""
        xs = [x for x, _ in self.flat]
        ys = [y for _, y in self.flat]
        span_x = (max(xs) - min(xs)) or 1.0
        span_y = (max(ys) - min(ys)) or 1.0
        # Room for the scale bar and its text at the bottom.
        room_w, room_h = width - 2 * PADDING, height - 2 * PADDING - 22
        scale = min(room_w / span_x, room_h / span_y)
        return (scale, width / 2 - (max(xs) + min(xs)) / 2 * scale,
                PADDING + room_h / 2 - (max(ys) + min(ys)) / 2 * scale)

    def _label(self, text):
        layout = self.create_pango_layout(text)
        attrs = Pango.AttrList()
        attrs.insert(Pango.attr_scale_new(0.8))
        layout.set_attributes(attrs)
        return layout

    def _text(self, snapshot, layout, x, y, color):
        snapshot.save()
        snapshot.translate(_point(x, y))
        snapshot.append_layout(layout, color)
        snapshot.restore()

    def do_snapshot(self, snapshot):
        width, height = self.get_width(), self.get_height()
        scale, dx, dy = self._fit(width, height)
        fg = self.get_color()
        dark = Adw.StyleManager.get_default().get_dark()
        accent = _rgba(ACCENT_DARK if dark else ACCENT)
        pixels = [(x * scale + dx, y * scale + dy) for x, y in self.flat]

        path = Gsk.PathBuilder.new()
        for n, (x, y) in enumerate(pixels):
            if n == 0 or n in self.breaks:
                path.move_to(x, y)
            else:
                path.line_to(x, y)
        stroke = Gsk.Stroke.new(3.0)
        stroke.set_line_join(Gsk.LineJoin.ROUND)
        stroke.set_line_cap(Gsk.LineCap.ROUND)
        snapshot.append_stroke(path.to_path(), stroke, accent)

        # Start: a dot; end: a square. Both are named, so the shape and
        # the word carry it, not a colour.
        for (x, y), name, start in ((pixels[0], "Start", True),
                                    (pixels[-1], "End", False)):
            mark = Gsk.PathBuilder.new()
            if start:
                mark.add_circle(_point(x, y), 6)
            else:
                mark.add_rect(_rect(x - 5, y - 5, 10, 10))
            snapshot.append_fill(mark.to_path(), Gsk.FillRule.WINDING, fg)
            layout = self._label(name)
            lw, lh = layout.get_pixel_size()
            lx = min(max(x + 9, 0), width - lw)
            ly = min(max(y - lh - 4 if start else y + 6, 0), height - lh)
            self._text(snapshot, layout, lx, ly, fg)

        # Scale bar, bottom left.
        metres = scale_length(width / scale)
        bar = metres * scale
        y = height - 12
        color = _with_alpha(fg, 0.7)
        snapshot.append_color(color, _rect(PADDING, y, bar, 2))
        for x in (PADDING, PADDING + bar - 2):
            snapshot.append_color(color, _rect(x, y - 4, 2, 6))
        layout = self._label(scale_text(metres))
        self._text(snapshot, layout, PADDING + bar + 6,
                   y - layout.get_pixel_size()[1] / 2, color)
