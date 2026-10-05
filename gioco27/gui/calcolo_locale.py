"""Annullamento cooperativo attraverso i callback gia' esposti dai calcoli."""


class CalcoloAnnullato(BaseException):
    # Non e' un errore del motore: non deve attivare fallback o nuovi calcoli.
    pass


def verifica_annullamento(event):
    if event.is_set():
        raise CalcoloAnnullato()
