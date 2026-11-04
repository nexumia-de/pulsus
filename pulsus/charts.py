"""Pulsus's chart widget, drawn with GTK's own paths (Gsk), so no plotting
library is bundled. Rules (docs/visualisation.md): one measure per
chart, bars start at zero, gaps in the data stay gaps, the normal range
is a band, the value under the finger is written out, and every chart
has a text alternative for screen readers.
"""
from dataclasses import dataclass, field

from gi.repository import Adw, Gdk, Graphene, Gsk, Gtk, Pango

from pulsus import stats

# The data colour: Pulsus's accent (style.css), lighter in dark mode so
# marks keep 3:1 against the card (docs/design.md). Data colours may be
# fixed (phosh-toolkit docs/design.md); text and grid use the theme's
# foreground colour.
ACCENT = "#c6345a"
ACCENT_DARK = "#ef7b9b"


def _rgba(spec, alpha=1.0):
    color = Gdk.RGBA()
    color.parse(spec)
    color.alpha *= alpha
    return color


def _with_alpha(color, alpha):
    result = color.copy()
    result.alpha *= alpha
    return result


def _point(x, y):
    p = Graphene.Point()
    p.init(x, y)
    return p


def _rect(x, y, w, h):
    r = Graphene.Rect()
    r.init(x, y, w, h)
    return r


@dataclass
class Series:
    """What one chart shows.

    points: (x, y or None); None is a gap.
    style: "bars", "dots" (with `average` as a line), "line", or
      "timeline" (`spans` as blocks, y unused).
    slots: x values are days (each one slot wide); otherwise x is
      continuous (seconds) between x_min and x_max.
    """
    points: list
    style: str
    x_min: float
    x_max: float
    y_format: object = str               # number -> axis text
    describe: object = None              # (x, y) -> text for the selection
    band: tuple = None                   # (low, high): the normal range
    goal: float = None                   # a dashed line, e.g. the step goal
    average: list = field(default_factory=list)   # (x, y or None)
    spans: list = field(default_factory=list)     # (x0, x1) for timeline
    x_labels: list = field(default_factory=list)  # (x, text)
    slots: bool = True
    gap: float = None                    # continuous lines break above it
    y_zero: bool = None                  # start the axis at 0 (bars: yes)
    summary: str = ""                    # the text alternative


class Chart(Gtk.Widget):
    __gtype_name__ = "PulsusChart"

    def __init__(self, height=180, compact=False):
        super().__init__(accessible_role=Gtk.AccessibleRole.IMG)
        self.height = height
        self.compact = compact
        self.series = None
        self.selected = None
        self.add_css_class("pulsus-chart")
        if not compact:
            click = Gtk.GestureClick()
            click.connect("pressed", self._on_pressed)
            # Tap only: a horizontal drag here would take the swipe back
            # away from the navigation view.
            self.add_controller(click)

    def set_series(self, series):
        self.series = series
        self.selected = None
        self.update_property([Gtk.AccessibleProperty.LABEL], [series.summary or ""])
        self.queue_draw()

    # --- size ----------------------------------------------------------

    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.VERTICAL:
            return self.height, self.height, -1, -1
        return 80, 320, -1, -1

    # --- geometry ------------------------------------------------------

    def _layout(self, text, scale=0.8, bold=False):
        layout = self.create_pango_layout(text)
        attrs = Pango.AttrList()
        attrs.insert(Pango.attr_scale_new(scale))
        attrs.insert(Pango.attr_font_features_new("tnum"))
        if bold:
            attrs.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
        layout.set_attributes(attrs)
        return layout

    def _y_axis(self):
        s = self.series
        values = [y for _, y in s.points if y is not None]
        values += [y for _, y in s.average if y is not None]
        if s.band:
            values += list(s.band)
        if s.goal is not None:
            values.append(s.goal)
        if not values:
            values = [0, 1]
        zero = s.y_zero if s.y_zero is not None else s.style == "bars"
        low = 0 if zero else min(values)
        high = max(values)
        if not zero:
            pad = (high - low) * 0.1 or 1
            low, high = low - pad, high + pad
        return stats.nice_ticks(low, high, 2 if self.compact else 4)

    def _frame(self, width, height):
        """(left, top, plot width, plot height) and the axis."""
        ticks, y0, y1 = self._y_axis()
        if self.compact:
            return (0, 2, width, height - 4), ticks, y0, y1
        if self.series.style == "timeline":
            return (8, 24, width - 16, height - 44), ticks, y0, y1
        label_width = max(self._layout(self.series.y_format(t)).get_pixel_size()[0]
                          for t in ticks) + 8
        top, bottom = 24, 20
        return (label_width, top, width - label_width - 2, height - top - bottom), \
            ticks, y0, y1

    def _x(self, x, frame):
        s = self.series
        left, _, w, _ = frame
        if s.slots:
            count = s.x_max - s.x_min + 1
            return left + (x - s.x_min + 0.5) / count * w
        span = (s.x_max - s.x_min) or 1
        return left + (x - s.x_min) / span * w

    def _slot_width(self, frame):
        s = self.series
        return frame[2] / (s.x_max - s.x_min + 1)

    # --- drawing -------------------------------------------------------

    def do_snapshot(self, snapshot):
        if self.series is None:
            return
        width, height = self.get_width(), self.get_height()
        frame, ticks, y0, y1 = self._frame(width, height)
        left, top, w, h = frame
        fg = self.get_color()
        dark = Adw.StyleManager.get_default().get_dark()
        accent = _rgba(ACCENT_DARK if dark else ACCENT)

        def y_px(y):
            return top + h - (y - y0) / ((y1 - y0) or 1) * h

        s = self.series
        # Grid and y labels (a timeline has no y axis).
        if not self.compact and s.style != "timeline":
            for t in ticks:
                py = y_px(t)
                snapshot.append_color(_with_alpha(fg, 0.12), _rect(left, py, w, 1))
                layout = self._layout(s.y_format(t))
                lw, lh = layout.get_pixel_size()
                self._text(snapshot, layout, left - lw - 6, py - lh / 2,
                           _with_alpha(fg, 0.6))
        # The normal range.
        if s.band:
            lo, hi = s.band
            snapshot.append_color(_with_alpha(accent, 0.16),
                                  _rect(left, y_px(hi), w, max(1, y_px(lo) - y_px(hi))))
        if s.style == "bars":
            self._bars(snapshot, frame, y_px, accent)
        elif s.style == "dots":
            self._dots(snapshot, frame, y_px, accent)
        elif s.style == "line":
            self._line(snapshot, frame, y_px, s.points, accent, 2.0)
        elif s.style == "timeline":
            for x0, x1 in s.spans:
                a, b = self._x(x0, frame), self._x(x1, frame)
                snapshot.append_color(accent, _rect(a, top + h * 0.25,
                                                    max(1.0, b - a), h * 0.5))
        if s.average:
            self._line(snapshot, frame, y_px, s.average, accent, 2.5)
        if s.goal is not None:
            path = Gsk.PathBuilder.new()
            path.move_to(left, y_px(s.goal))
            path.line_to(left + w, y_px(s.goal))
            stroke = Gsk.Stroke.new(1.5)
            stroke.set_dash([5, 4])
            snapshot.append_stroke(path.to_path(), stroke, _with_alpha(fg, 0.7))
        if not self.compact:
            self._x_labels(snapshot, frame, fg)
            self._selection(snapshot, frame, y_px, fg)

    def _text(self, snapshot, layout, x, y, color):
        snapshot.save()
        snapshot.translate(_point(x, y))
        snapshot.append_layout(layout, color)
        snapshot.restore()

    def _bars(self, snapshot, frame, y_px, accent):
        _, top, _, h = frame
        slot = self._slot_width(frame)
        bar = max(1.0, min(slot * 0.7, 28))
        base = y_px(max(self._y_axis()[1], 0))
        for x, y in self.series.points:
            if y is None or y <= 0:
                continue
            cx = self._x(x, frame)
            py = y_px(y)
            color = accent if self.selected in (None, x) else _with_alpha(accent, 0.45)
            path = Gsk.PathBuilder.new()
            rounded = Gsk.RoundedRect()
            radius = Graphene.Size()
            radius.init(min(3, bar / 2), min(3, bar / 2))
            zero = Graphene.Size()
            zero.init(0, 0)
            rounded.init(_rect(cx - bar / 2, py, bar, max(1.0, base - py)),
                         radius, radius, zero, zero)
            path.add_rounded_rect(rounded)
            snapshot.append_fill(path.to_path(), Gsk.FillRule.WINDING, color)

    def _dots(self, snapshot, frame, y_px, accent):
        radius = 2.5 if self.compact else 3.5
        path = Gsk.PathBuilder.new()
        for x, y in self.series.points:
            if y is not None:
                path.add_circle(_point(self._x(x, frame), y_px(y)), radius)
        alpha = 1.0 if not self.series.average else 0.45
        snapshot.append_fill(path.to_path(), Gsk.FillRule.WINDING,
                             _with_alpha(accent, alpha))

    def _line(self, snapshot, frame, y_px, points, color, width):
        s = self.series
        path = Gsk.PathBuilder.new()
        previous = None
        drawn = False
        for x, y in points:
            if y is None:
                previous = None
                continue
            px, py = self._x(x, frame), y_px(y)
            joined = previous is not None and (
                s.gap is None or x - previous <= s.gap)
            if joined:
                path.line_to(px, py)
            else:
                path.move_to(px, py)
            previous = x
            drawn = True
        if drawn:
            stroke = Gsk.Stroke.new(width)
            stroke.set_line_join(Gsk.LineJoin.ROUND)
            stroke.set_line_cap(Gsk.LineCap.ROUND)
            snapshot.append_stroke(path.to_path(), stroke, color)

    def _x_labels(self, snapshot, frame, fg):
        _, top, w, h = frame
        right = -1e9
        for x, label in self.series.x_labels:
            layout = self._layout(label)
            lw, _ = layout.get_pixel_size()
            px = self._x(x, frame) - lw / 2
            px = min(max(px, 0), self.get_width() - lw)
            if px < right + 6:
                continue
            self._text(snapshot, layout, px, top + h + 4, _with_alpha(fg, 0.6))
            right = px + lw

    def _selection(self, snapshot, frame, y_px, fg):
        s = self.series
        if self.selected is None or s.describe is None:
            return
        point = next(((x, y) for x, y in s.points if x == self.selected), None)
        if point is None:
            return
        left, top, w, h = frame
        px = self._x(point[0], frame)
        snapshot.append_color(_with_alpha(fg, 0.5), _rect(px - 0.5, top, 1, h))
        layout = self._layout(s.describe(*point), scale=0.85, bold=True)
        lw, lh = layout.get_pixel_size()
        lx = min(max(px - lw / 2, 0), self.get_width() - lw)
        self._text(snapshot, layout, lx, max(0, top - lh - 4), fg)

    # --- touch ---------------------------------------------------------

    def _select_at(self, x):
        s = self.series
        if s is None or not s.points or s.describe is None:
            return
        frame = self._frame(self.get_width(), self.get_height())[0]
        candidates = [p for p in s.points if p[1] is not None] or s.points
        nearest = min(candidates, key=lambda p: abs(self._x(p[0], frame) - x))
        if nearest[0] != self.selected:
            self.selected = nearest[0]
            self.queue_draw()

    def _on_pressed(self, gesture, n, x, y):
        self._select_at(x)
