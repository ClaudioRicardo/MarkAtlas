"""Diálogos modais reutilizáveis para confirmação e entrada de texto."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    Gtk = object  # type: ignore


def show_confirm_dialog(parent: Optional[object], title: str, message: str) -> bool:
    """
    Exibe um diálogo modal de confirmação com botões Cancelar e Confirmar/Excluir.
    
    :param parent: Janela pai
    :param title: Título do diálogo
    :param message: Mensagem detalhada
    :return: True se confirmado, False se cancelado
    """
    if not GTK_AVAILABLE:
        return True

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=Gtk.DialogFlags.MODAL,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        text=title,
    )
    dialog.format_secondary_text(message)
    dialog.get_widget_for_response(Gtk.ResponseType.OK).get_style_context().add_class("btn-primary")

    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def show_prompt_dialog(
    parent: Optional[object],
    title: str,
    prompt_text: str,
    default_text: str = "",
) -> Optional[str]:
    """
    Exibe um diálogo modal solicitando ao usuário que insira um texto (ex: nome de nova pasta).
    
    :param parent: Janela pai
    :param title: Título da janela de diálogo
    :param prompt_text: Rótulo / instrução para o campo
    :param default_text: Valor inicial no campo de texto
    :return: String informada pelo usuário ou None se cancelado
    """
    if not GTK_AVAILABLE:
        return default_text

    dialog = Gtk.Dialog(
        title=title,
        transient_for=parent,
        flags=Gtk.DialogFlags.MODAL,
    )
    dialog.set_default_size(350, 150)
    dialog.add_buttons(
        "Cancelar", Gtk.ResponseType.CANCEL,
        "Criar", Gtk.ResponseType.OK,
    )

    box = dialog.get_content_area()
    box.set_spacing(10)
    box.set_border_width(14)

    lbl = Gtk.Label(label=prompt_text)
    lbl.set_xalign(0.0)
    box.pack_start(lbl, False, False, 0)

    entry = Gtk.Entry()
    entry.set_text(default_text)
    entry.set_activates_default(True)
    box.pack_start(entry, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()

    response = dialog.run()
    entered_text = entry.get_text().strip()
    dialog.destroy()

    if response == Gtk.ResponseType.OK and entered_text:
        return entered_text
    return None
