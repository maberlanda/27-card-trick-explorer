"""Attach the shared catalog to controls, tab labels, headings and menus.

Bindings are scoped to their actual area: identically named Calculate/Reset
commands do not accidentally acquire the explanation of a different tool.
Existing useful tooltips are retained. Standard scrollbars/text selection and
ordinary Close controls are deliberately excluded.
"""
import tkinter as tk
from tkinter import ttk
from ..i18n import _UX4_TIPS
from .i18n import tr, CATALOGS, get_language
from .tooltip import attach


def normalise(text):
    value = " ".join(str(text).strip().split())
    while value and not value[0].isalnum() and value[0] != "#":
        value = value[1:].lstrip()
    return value


def tip(scope, key):
    return tr(f"ux4.tip.{list(_UX4_TIPS).index((scope, key))}")


def install(root, scope):
    catalog = CATALOGS[get_language()]
    labels = {}
    for number, (area, key) in enumerate(_UX4_TIPS):
        if area in ("*", scope) and (key in catalog or key.startswith("@")):
            labels[normalise(key[1:] if key.startswith("@") else tr(key))] = tr(f"ux4.tip.{number}")

    def lookup(label):
        return labels.get(normalise(label))

    def visit(widget):
        if isinstance(widget, ttk.Notebook):
            tips = {tab: lookup(widget.tab(tab, "text")) for tab in widget.tabs()}
            _regions(widget, tips, notebook=True)
        elif isinstance(widget, ttk.Treeview):
            tips = {f"#{n}": lookup(widget.heading(col, "text"))
                    for n, col in enumerate(("#0", *widget["columns"]))}
            _regions(widget, tips)
        elif isinstance(widget, tk.Menu):
            _menu(widget, lookup)
        elif isinstance(widget, tk.Listbox):
            tips = {index: lookup(widget.get(index)) for index in range(widget.size())}
            if any(tips.values()):
                attach(widget, lambda: tips.get(widget.curselection()[0] if widget.curselection() else 0))
                def hover(event, box=widget, values=tips):
                    box._tooltip.set_text(values.get(box.nearest(event.y)))
                    box._tooltip._schedule()
                widget.bind("<Motion>", hover, add="+")
                widget.bind("<FocusIn>", lambda e, box=widget, values=tips:
                            box._tooltip.set_text(values.get(box.curselection()[0] if box.curselection() else 0)), add="+")
                widget.bind("<<ListboxSelect>>", lambda e, box=widget, values=tips:
                            box._tooltip.set_text(values.get(box.curselection()[0] if box.curselection() else 0)), add="+")
        elif "text" in widget.keys() and not getattr(widget, "_tooltip", None):
            tip = lookup(widget.cget("text"))
            if tip:
                attach(widget, tip)
                if isinstance(widget, (tk.Label, ttk.Label)):
                    siblings = widget.master.winfo_children()
                    next_widgets = siblings[siblings.index(widget) + 1:]
                    if next_widgets and isinstance(next_widgets[0],
                            (ttk.Entry, ttk.Combobox, ttk.Spinbox, ttk.Scale, ttk.Checkbutton, tk.Text)):
                        target = next_widgets[0]
                        if not getattr(target, "_tooltip", None):
                            attach(target, tip)
        for child in widget.winfo_children():
            visit(child)
    visit(root)
    return labels


def _regions(widget, tips, notebook=False):
    tips = {key: value for key, value in tips.items() if value}
    if not tips:
        return
    fallback = "\n".join(dict.fromkeys(tips.values()))
    previous = getattr(widget, "_tooltip", None)
    body = previous.text if previous and not callable(previous.text) else getattr(widget, "_guidance_body", None)
    widget._guidance_body = body
    if body:
        fallback = body
    for sequence, binding in getattr(widget, "_guidance_bindings", []):
        widget.unbind(sequence, binding)
    widget._guidance_bindings = []
    current = {"text": fallback}
    tooltip = attach(widget, lambda: current["text"])
    widget._guidance_regions = tips

    def motion(event):
        key = None
        if notebook:
            try:
                key = widget.tabs()[widget.index(f"@{event.x},{event.y}")]
            except tk.TclError:
                pass
        elif widget.identify_region(event.x, event.y) == "heading":
            key = widget.identify_column(event.x)
        value = tips.get(key, body)
        if value != current["text"]:
            tooltip._hide()
            current["text"] = value
            if value:
                tooltip._schedule()
    widget._guidance_bindings.append(("<Motion>", widget.bind("<Motion>", motion, add="+")))
    def focus(event=None):
        current["text"] = tips.get(widget.select(), fallback) if notebook else fallback
    widget._guidance_bindings.append(("<FocusIn>", widget.bind("<FocusIn>", focus, add="+")))
    if notebook:
        widget._guidance_bindings.append(("<<NotebookTabChanged>>", widget.bind("<<NotebookTabChanged>>", focus, add="+")))


def _menu(menu, lookup):
    values = {}
    end = menu.index("end")
    for index in range((end if end is not None else -1) + 1):
        if menu.type(index) != "separator":
            value = lookup(menu.entrycget(index, "label"))
            if value:
                values[index] = value
    if not values:
        return
    tip = attach(menu, "")

    def selected(event=None):
        tip._hide()
        tip.set_text(values.get(menu.index("active"), ""))
        tip._schedule_dal_focus()
    menu.bind("<<MenuSelect>>", selected, add="+")
    menu.bind("<Unmap>", tip._hide, add="+")


def fields(owner, mapping):
    """Explicit associations for controls whose text lives in a nearby label."""
    for attr, key in mapping.items():
        widget = getattr(owner, attr, None)
        if isinstance(widget, tk.Misc) and not getattr(widget, "_tooltip", None):
            attach(widget, tip(*key) if isinstance(key, tuple) else tr(key))
