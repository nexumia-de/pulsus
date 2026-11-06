"""The first page: one card per metric for the chosen day, each with the
number, a short context line and the last seven days, opening its page
(docs/visualisation.md#today)."""
from datetime import date, datetime, timedelta
from statistics import fmean

from gi.repository import Adw, Gtk

from pulsus import NAME, stats, text
from pulsus.card import Card
from pulsus.charts import Series
from pulsus.metrics import METRICS
from pulsus.workouts import kind_name

# A banner when Amazfish has not stored anything for this long.
STALE = timedelta(hours=24)


def spark_series(daily, day, style):
    span = [day - timedelta(days=6 - n) for n in range(7)]
    return Series([(n, daily.get(d)) for n, d in enumerate(span)],
                  "bars" if style == "bars" else "dots", 0, 6)


class TodayPage(Adw.NavigationPage):
    def __init__(self, window):
        super().__init__(title=NAME, tag="today")
        self.window = window
        self.day = date.today()
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.title = Adw.WindowTitle(title="Today")
        header.set_title_widget(self.title)
        self.previous = Gtk.Button(icon_name="go-previous-symbolic",
                                   tooltip_text="Previous Day")
        self.previous.update_property([Gtk.AccessibleProperty.LABEL], ["Previous Day"])
        self.previous.connect("clicked", lambda *_: self.show_day(self.day - timedelta(days=1)))
        self.next = Gtk.Button(icon_name="go-next-symbolic", tooltip_text="Next Day")
        self.next.update_property([Gtk.AccessibleProperty.LABEL], ["Next Day"])
        self.next.connect("clicked", lambda *_: self.show_day(self.day + timedelta(days=1)))
        header.pack_start(self.previous)
        header.pack_start(self.next)
        menu = Gtk.MenuButton(icon_name="open-menu-symbolic", tooltip_text="Main Menu",
                              primary=True, menu_model=window.menu_model())
        menu.update_property([Gtk.AccessibleProperty.LABEL], ["Main Menu"])
        header.pack_end(menu)
        toolbar.add_top_bar(header)
        self.banner = Adw.Banner()
        toolbar.add_top_bar(self.banner)

        self.cards = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                                 homogeneous=True, max_children_per_line=3,
                                 column_spacing=12, row_spacing=12,
                                 valign=Gtk.Align.START)
        self.cards.add_css_class("pulsus-cards")
        self.metric_cards = {}
        for metric in METRICS:
            card = Card(metric.title, metric.icon)
            card.connect("clicked", self._on_metric, metric)
            self.metric_cards[metric.id] = card
            self.cards.append(card)
        self.workout_card = Card("Workouts", "pulsus-workout-symbolic")
        self.workout_card.connect("clicked", lambda *_: window.show_workouts())
        self.cards.append(self.workout_card)
        for child in list(_children(self.cards)):
            child.set_focusable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=12, margin_bottom=24, margin_start=12, margin_end=12)
        box.append(self.cards)
        self.status = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER,
                                css_classes=["caption", "dimmed"])
        box.append(self.status)
        clamp = Adw.Clamp(maximum_size=1100, child=box)
        toolbar.set_content(Gtk.ScrolledWindow(
            child=clamp, hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.set_child(toolbar)
        self.refresh()

    def show_day(self, day):
        self.day = min(day, date.today())
        self.refresh()

    def _on_metric(self, card, metric):
        self.window.show_metric(metric.id, self.day)

    # --- filling the cards ---------------------------------------------

    def refresh(self):
        store = self.window.source.store
        if store is None:
            return
        today = date.today()
        if self.day > today:
            self.day = today
        self.title.set_title(text.day(self.day))
        self.title.set_subtitle("" if self.day == today else f"{self.day:%A}")
        self.next.set_sensitive(self.day < today)
        first = store.first_day()
        self.previous.set_sensitive(first is None or self.day > first)
        since = self.day - timedelta(days=stats.BASELINE_DAYS + 7)
        for metric in METRICS:
            card = self.metric_cards[metric.id]
            visible = store.has(metric.table) and bool(
                getattr(store, metric.daily)(since, today))
            card.get_parent().set_visible(visible)
            if visible:
                getattr(self, "_fill_" + metric.id.replace("-", "_"),
                        self._fill_level)(store, metric, card)
        self._fill_workout(store)
        last = store.last_sample()
        now = datetime.now()
        if last is None:
            self.status.set_label("Amazfish has not stored any data yet.")
        else:
            self.status.set_label(f"Newest data from Amazfish: {text.ago(last, now)}. "
                                  "Watch Health only shows what Amazfish has downloaded "
                                  "from the watch.")
        stale = last is None or now - last > STALE
        self.banner.set_title(
            "No new data from Amazfish for over a day. Open Amazfish to sync the watch."
            if stale else "")
        self.banner.set_revealed(stale)

    def _daily(self, store, metric):
        raw = getattr(store, metric.daily)(self.day - timedelta(days=35), self.day)
        return {d: metric.value(v) for d, v in raw.items()}

    def _fill_steps(self, store, metric, card):
        daily = self._daily(store, metric)
        goal = self.window.settings.step_goal
        steps = daily.get(self.day)
        card.progress.set_visible(steps is not None)
        if steps is None:
            card.show("–", "", "No steps stored for this day.",
                      spark_series(daily, self.day, "bars"), "no data")
            return
        card.progress.set_fraction(min(1.0, steps / goal))
        card.show(text.number(steps), "steps",
                  f"{steps / goal:.0%} of your goal of {text.number(goal)}.",
                  spark_series(daily, self.day, "bars"))

    def _fill_heart_rate(self, store, metric, card):
        daily = self._daily(store, metric)
        value = daily.get(self.day)
        latest = None
        if self.day == date.today():
            for minute in reversed(store.day_minutes(self.day)):
                if minute.heart_rate is not None:
                    latest = minute
                    break
        if value is None:
            card.show("–", "", "No heart rate stored for this day.",
                      spark_series(daily, self.day, "dots"), "no data")
            return
        context = self._normal(metric, daily, value)
        if latest is not None:
            context = (f"Latest {latest.heart_rate} bpm at "
                       f"{text.clock(datetime.fromtimestamp(latest.ts))}. " + context)
        card.show(text.number(value), "bpm resting", context.strip(),
                  spark_series(daily, self.day, "dots"))

    def _fill_sleep(self, store, metric, card):
        sleep = store.sleeps(self.day - timedelta(days=35), self.day)
        daily = {d: s.asleep.total_seconds() / 3600 for d, s in sleep.items()}
        night = sleep.get(self.day)
        if night is None:
            card.show("–", "", "No sleep stored for last night.",
                      spark_series(daily, self.day, "bars"), "no data")
            return
        earlier = [v for d, v in daily.items() if d < self.day]
        context = f"{text.clock(night.start)}–{text.clock(night.end)}."
        if len(earlier) >= stats.BASELINE_MIN_DAYS:
            typical = fmean(earlier[-stats.BASELINE_DAYS:])
            context += f" Your average is {text.duration_hours(typical)}."
        card.show(text.duration(night.asleep), "asleep", context,
                  spark_series(daily, self.day, "bars"))

    def _fill_pai(self, store, metric, card):
        raw = store.daily_pai(self.day - timedelta(days=7), self.day)
        daily = {d: v[1] for d, v in raw.items()}
        if self.day not in raw:
            card.show("–", "", "No PAI stored for this day.",
                      spark_series(daily, self.day, "dots"), "no data")
            return
        earned, total = raw[self.day]
        card.progress.set_visible(True)
        card.progress.set_fraction(min(1.0, total / 100))
        card.show(text.number(total), "PAI",
                  f"Last 7 days, {text.number(earned)} earned on this day. "
                  "The watch suggests 100.", spark_series(daily, self.day, "dots"))

    def _fill_level(self, store, metric, card):
        daily = self._daily(store, metric)
        value = daily.get(self.day)
        if value is None:
            card.show("–", "", f"No {metric.what} stored for this day.",
                      spark_series(daily, self.day, "dots"), "no data")
            return
        card.show(metric.format(value), metric.unit or "average",
                  self._normal(metric, daily, value),
                  spark_series(daily, self.day, "dots"))

    def _normal(self, metric, daily, value):
        """Where the value sits in the user's normal range, as text."""
        if not metric.baseline:
            return ""
        band = stats.baseline(daily, self.day)
        if band is None:
            return "Your normal range shows after 14 days of data."
        low, high = band
        where = "within" if low <= value <= high else \
            "below" if value < low else "above"
        unit = f" {metric.unit}" if metric.unit else ""
        return (f"{where.capitalize()} your normal range of "
                f"{metric.format(low)}–{metric.format(high)}{unit}.")

    def _fill_workout(self, store):
        workouts = store.workouts(limit=1)
        self.workout_card.get_parent().set_visible(bool(workouts))
        if not workouts:
            return
        w = workouts[0]
        distance = w.number("distanceMeters")
        parts = [text.day(w.start.date()), text.clock(w.start)]
        if distance:
            parts.append(f"{distance / 1000:.2f} km")
        self.workout_card.show(text.duration(w.duration), kind_name(w),
                               " · ".join(parts))


def _children(flowbox):
    child = flowbox.get_first_child()
    while child is not None:
        yield child
        child = child.get_next_sibling()
