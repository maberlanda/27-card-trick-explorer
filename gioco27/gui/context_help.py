"""Shared operational help: one source per topic, reusable inline banners."""
from .i18n import tr
from .help_banner import HelpBanner

TOPICS = {
    "A01": "s02", "A02": "s01", "A03": "i2t", "A04": "s04",
    "A05": "i3", "A06": "i4", "A06b": "s16", "A07": "s17",
    "A08": "i5", "A09": "s20", "A10": "i6", "A10b": "s16",
    "A11": "s32", "A12": "s29", "A13": "s27",
}
AREAS = {
    "simulatore": ("A01", "A02", "A05"), "tavola": ("A01", "A02", "A08", "A09"),
    "explorer": ("A03", "A06b", "A07"), "anteprima": ("A03", "A04"),
    "analisi": ("A03",), "cicli": ("A09",), "distribuzione": ("A10b",),
}


def text(topics):
    return "\n\n".join(tr(f"ux4.help.{topic}.title") + "\n" +
                         tr(f"ux4.help.{topic}.body") for topic in topics)


def banner(parent, topic, on_open_guide=None, short=None):
    if on_open_guide is None:
        owner = parent
        while owner is not None and on_open_guide is None:
            on_open_guide = getattr(owner, "_open_guide", None)
            owner = getattr(owner, "master", None)
    return HelpBanner(parent, short or tr(f"ux4.help.{topic}.title"), text((topic,)),
                      on_open_guide, TOPICS[topic])
