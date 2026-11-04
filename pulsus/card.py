"""A card of the Today page: a tappable card with icon and title, value
and unit, a context line, an optional progress bar and a sparkline."""
from gi.repository import Gtk

from pulsus.charts import Chart


def _label(value, classes=(), **kw):
    kw.setdefault("xalign", 0)
    label = Gtk.Label(label=value, **kw)
    for c in classes:
        label.add_css_class(c)
    return label


class Card(Gtk.Button):
    """A tappable card: icon and title, value and unit, context, sparkline."""

    def __init__(self, title, icon):
        super().__init__()
        self.add_css_class("card")
        self.add_css_class("pulsus-card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        head = Gtk.Box(spacing=8)
        head.append(Gtk.Image(icon_name=icon, accessible_role=Gtk.AccessibleRole.PRESENTATION))
        head.append(_label(title, ("heading",), hexpand=True))
        head.append(Gtk.Image(icon_name="go-next-symbolic",
                              accessible_role=Gtk.AccessibleRole.PRESENTATION))
        box.append(head)
        value_box = Gtk.Box(spacing=6)
        self.value = _label("", ("title-1", "numeric"))
        self.unit = _label("", ("dimmed",), valign=Gtk.Align.BASELINE_FILL)
        value_box.append(self.value)
        value_box.append(self.unit)
        box.append(value_box)
        # A short natural width, so the flow box puts cards side by side.
        self.context = _label("", ("dimmed",), wrap=True, max_width_chars=30,
                              width_chars=20)
        box.append(self.context)
        self.progress = Gtk.ProgressBar(visible=False)
        box.append(self.progress)
        self.spark = Chart(height=44, compact=True)
        box.append(self.spark)
        self.set_child(box)
        self.title = title

    def show(self, value, unit, context, spark=None, accessible=""):
        self.value.set_label(value)
        self.unit.set_label(unit)
        self.context.set_label(context)
        self.context.set_visible(bool(context))
        self.spark.set_visible(spark is not None)
        if spark is not None:
            self.spark.set_series(spark)
        self.update_property([Gtk.AccessibleProperty.LABEL],
                             [f"{self.title}: {accessible or value + ' ' + unit}. {context}"])
