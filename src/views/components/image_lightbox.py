"""Diálogo modal (Lightbox) para visualização ampliada de imagens e diagramas com controles de zoom."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gtk, Gdk, GdkPixbuf
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    Gtk = object  # type: ignore


class ImageLightboxDialog(Gtk.Dialog if GTK_AVAILABLE else object):  # type: ignore
    """Modal flutuante de visualização e inspeção de imagens e diagramas em alta resolução."""

    def __init__(
        self,
        parent: Optional[object] = None,
        image_path: str = "",
        title: Optional[str] = None,
    ) -> None:
        self.image_path = image_path
        self._custom_title = title or (Path(image_path).name if image_path else "Visualização de Imagem")
        self._current_zoom = 1.0
        self._original_pixbuf: Optional[object] = None

        if not GTK_AVAILABLE:
            return

        super().__init__(
            title=self._custom_title,
            transient_for=parent if isinstance(parent, Gtk.Window) else None,
            modal=True,
            destroy_with_parent=True,
        )

        self.get_style_context().add_class("image-lightbox-dialog")
        self.set_default_size(980, 680)
        self.connect("key-press-event", self._on_key_press)

        self._build_ui()
        self._load_image()

    def _build_ui(self) -> None:
        """Constrói a barra de ferramentas de zoom e a área de rolagem da imagem."""
        content_area = self.get_content_area()
        content_area.set_spacing(0)

        # 1. Barra de Ferramentas Superior
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.get_style_context().add_class("lightbox-toolbar")

        # Título da imagem
        lbl_title = Gtk.Label(label=f"🖼️ {self._custom_title}")
        lbl_title.set_xalign(0.0)
        lbl_title.get_style_context().add_class("lightbox-title")
        toolbar.pack_start(lbl_title, True, True, 0)

        # Controles de Zoom
        btn_zoom_out = Gtk.Button(label="➖")
        btn_zoom_out.set_tooltip_text("Reduzir Zoom (-25%)")
        btn_zoom_out.get_style_context().add_class("btn-lightbox")
        btn_zoom_out.connect("clicked", lambda _: self.zoom_out())
        toolbar.pack_start(btn_zoom_out, False, False, 0)

        self._lbl_zoom = Gtk.Label(label="100%")
        self._lbl_zoom.get_style_context().add_class("lightbox-zoom-label")
        toolbar.pack_start(self._lbl_zoom, False, False, 0)

        btn_zoom_in = Gtk.Button(label="➕")
        btn_zoom_in.set_tooltip_text("Aumentar Zoom (+25%)")
        btn_zoom_in.get_style_context().add_class("btn-lightbox")
        btn_zoom_in.connect("clicked", lambda _: self.zoom_in())
        toolbar.pack_start(btn_zoom_in, False, False, 0)

        btn_fit = Gtk.Button(label="🔄 Ajustar")
        btn_fit.set_tooltip_text("Ajustar à Janela")
        btn_fit.get_style_context().add_class("btn-lightbox")
        btn_fit.connect("clicked", lambda _: self.zoom_fit())
        toolbar.pack_start(btn_fit, False, False, 0)

        btn_100 = Gtk.Button(label="📐 100%")
        btn_100.set_tooltip_text("Tamanho Original (100%)")
        btn_100.get_style_context().add_class("btn-lightbox")
        btn_100.connect("clicked", lambda _: self.zoom_reset())
        toolbar.pack_start(btn_100, False, False, 0)

        # Botão Fechar
        btn_close = Gtk.Button(label="✖ Fechar")
        btn_close.get_style_context().add_class("btn-lightbox-close")
        btn_close.connect("clicked", lambda _: self.destroy())
        toolbar.pack_start(btn_close, False, False, 4)

        content_area.pack_start(toolbar, False, False, 0)

        # 2. Área de Rolagem Centralizada
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.get_style_context().add_class("lightbox-scrolled")

        self._image_widget = Gtk.Image()
        self._image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._image_box.set_halign(Gtk.Align.CENTER)
        self._image_box.set_valign(Gtk.Align.CENTER)
        self._image_box.pack_start(self._image_widget, True, True, 16)

        self._scrolled_window.add(self._image_box)
        content_area.pack_start(self._scrolled_window, True, True, 0)

        self.show_all()

    def _load_image(self) -> None:
        """Carrega a imagem do disco em escala original."""
        if not self.image_path:
            return

        file_path = Path(self.image_path)
        if not file_path.exists() or not file_path.is_file():
            logger.warning(f"Arquivo de imagem não encontrado para lightbox: {self.image_path}")
            return

        try:
            # Carrega a imagem original com alta fidelidade
            self._original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(file_path))
            self._apply_zoom()
        except Exception as e:
            logger.error(f"Falha ao carregar imagem para lightbox {self.image_path}: {e}")

    def _apply_zoom(self) -> None:
        """Aplica o fator de zoom atual e atualiza o widget de imagem."""
        if not self._original_pixbuf or not GTK_AVAILABLE:
            return

        orig_w = self._original_pixbuf.get_width()
        orig_h = self._original_pixbuf.get_height()

        target_w = max(32, int(orig_w * self._current_zoom))
        target_h = max(32, int(orig_h * self._current_zoom))

        try:
            if target_w == orig_w and target_h == orig_h:
                scaled_pixbuf = self._original_pixbuf
            else:
                scaled_pixbuf = self._original_pixbuf.scale_simple(
                    target_w, target_h, GdkPixbuf.InterpType.BILINEAR
                )

            self._image_widget.set_from_pixbuf(scaled_pixbuf)
            self._lbl_zoom.set_label(f"{int(self._current_zoom * 100)}%")
        except Exception as e:
            logger.error(f"Erro ao redimensionar imagem no lightbox: {e}")

    def zoom_in(self) -> None:
        """Aumenta o zoom em +25% até o máximo de 400%."""
        if self._current_zoom < 4.0:
            self._current_zoom = min(4.0, self._current_zoom + 0.25)
            self._apply_zoom()

    def zoom_out(self) -> None:
        """Diminui o zoom em -25% até o mínimo de 25%."""
        if self._current_zoom > 0.25:
            self._current_zoom = max(0.25, self._current_zoom - 0.25)
            self._apply_zoom()

    def zoom_reset(self) -> None:
        """Redefine o zoom para 100% (tamanho original)."""
        self._current_zoom = 1.0
        self._apply_zoom()

    def zoom_fit(self) -> None:
        """Ajusta o zoom proporcionalmente para caber na janela visível."""
        if not self._original_pixbuf or not GTK_AVAILABLE:
            return

        alloc = self._scrolled_window.get_allocation()
        avail_w = max(200, alloc.width - 64)
        avail_h = max(200, alloc.height - 64)

        orig_w = self._original_pixbuf.get_width()
        orig_h = self._original_pixbuf.get_height()

        if orig_w > 0 and orig_h > 0:
            scale_w = avail_w / orig_w
            scale_h = avail_h / orig_h
            fit_scale = min(scale_w, scale_h, 1.0)
            self._current_zoom = max(0.25, round(fit_scale, 2))
            self._apply_zoom()

    def _on_key_press(self, widget: object, event: object) -> bool:
        """Fecha o modal ao pressionar ESC."""
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False
