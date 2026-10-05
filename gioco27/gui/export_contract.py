"""Preflight e riepilogo comuni agli export in cartella."""
from pathlib import Path
from tkinter import messagebox

from ..core.parallel import atomic_write
from .dialoghi_stato import _scegli
from .i18n import tr


def conferma_piano(parent, paths, omissions=()):
    conflicts = [str(p) for p in paths if Path(p).exists()]
    text = tr("ux2.export.plan", count=len(paths), files="\n".join(map(str, paths)))
    if omissions:
        text += "\n\n" + tr("ux2.export.omitted", detail="\n".join(omissions))
    if conflicts:
        text += "\n\n" + tr("ux2.export.conflicts", files="\n".join(conflicts))
    return _scegli(parent, tr("ux2.export.review"), text,
                   ((True, "ux2.export.overwrite" if conflicts else "button.export"),
                    (False, "button.cancel"))) is True


def riepilogo(parent, created, omissions=()):
    text = tr("ux2.export.created", count=len(created), files="\n".join(map(str, created)))
    if omissions:
        text += "\n\n" + tr("ux2.export.omitted", detail="\n".join(omissions))
    show = messagebox.showwarning if omissions or not created else messagebox.showinfo
    show(tr("ux2.export.report"), text, parent=parent)


def esporta_cartella(parent, folder, contents, omissions=()):
    """Il piano contiene testi gia' generati; nessuna scrittura prima della conferma."""
    paths = [(Path(folder) / name, content) for name, content in contents]
    omissions = list(omissions)
    if not paths:
        riepilogo(parent, [], omissions or [tr("export.no_content_selected")])
        return
    if not conferma_piano(parent, [p for p, _ in paths], omissions):
        return
    created = []
    for i, (path, content) in enumerate(paths):
        try:
            with atomic_write(path, "w", encoding="utf-8") as file:
                file.write(content)
            created.append(path)
        except OSError as exc:
            omissions.append(f"{path.name}: {exc}")
            omissions.extend(tr("ux2.export.not_written", name=p.name) for p, _ in paths[i+1:])
            break
    riepilogo(parent, created, omissions)
