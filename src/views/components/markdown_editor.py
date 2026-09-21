"""Componente de Editor Markdown com Live Preview sincronizado, renderização de imagens, links clicáveis e âncoras de footnotes."""

from __future__ import annotations

import logging
import re
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from src.core.config import default_config
from src.services.markdown_service import MarkdownService
from src.services.markdown.theme_colors import ThemeColors

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    Gtk = object  # type: ignore


class MarkdownEditorView(Gtk.Box if GTK_AVAILABLE else object):  # type: ignore
    """Componente integrado de Edição e Live Preview em Markdown com histórico Undo/Redo e atalhos completos."""

    MODE_SPLIT = "split"
    MODE_EDITOR = "editor"
    MODE_PREVIEW = "preview"

    def __init__(
        self,
        on_save_requested: Optional[Callable[[str, str], None]] = None,
        on_content_changed: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        if not GTK_AVAILABLE:
            self.on_save_requested = on_save_requested
            self.on_content_changed = on_content_changed
            self._current_note_path: Optional[str] = None
            self._raw_title: str = ""
            self._raw_content: str = ""
            self.markdown_service = MarkdownService()
            return

        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.get_style_context().add_class("editor-container")

        self.on_save_requested = on_save_requested
        self.on_content_changed = on_content_changed
        self.markdown_service = MarkdownService()

        self._current_mode = self.MODE_SPLIT
        self._debounce_timer_id: Optional[int] = None
        self._is_updating_programmatically = False

        # Pilhas de histórico para Undo / Redo
        self._undo_stack: List[str] = []
        self._redo_stack: List[str] = []
        self._current_note_path: Optional[str] = None
        self._font_size: int = default_config.font_size
        self._font_css_provider: Optional[Gtk.CssProvider] = None

        self._build_ui()
        self.apply_font_size(self._font_size)

    def _build_ui(self) -> None:
        """Constrói o layout com barra de ferramentas, entrada de título, painel dividido e barra de status do editor."""
        # 1. Barra de Ferramentas Superior do Editor
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar_box.get_style_context().add_class("editor-toolbar")

        # Entrada do Título da Nota
        self._title_entry = Gtk.Entry()
        self._title_entry.set_placeholder_text("Título da Nota...")
        self._title_entry.get_style_context().add_class("note-title-entry")
        self._title_entry.connect("key-press-event", self._on_key_press_event)
        self._title_entry.connect("changed", self._on_text_changed)
        toolbar_box.pack_start(self._title_entry, True, True, 0)

        # Seletor de Modo de Exibição (Split / Editor / Preview)
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        mode_box.get_style_context().add_class("mode-switcher-box")

        self._btn_split = Gtk.RadioButton.new_with_label(None, "📑 Lado a Lado")
        self._btn_split.set_mode(False)
        self._btn_split.get_style_context().add_class("btn-mode")
        self._btn_split.set_active(True)
        self._btn_split.connect("toggled", lambda b: self._on_mode_toggled(b, self.MODE_SPLIT))
        mode_box.pack_start(self._btn_split, False, False, 0)

        self._btn_editor = Gtk.RadioButton.new_with_label_from_widget(self._btn_split, "✏️ Editor")
        self._btn_editor.set_mode(False)
        self._btn_editor.get_style_context().add_class("btn-mode")
        self._btn_editor.connect("toggled", lambda b: self._on_mode_toggled(b, self.MODE_EDITOR))
        mode_box.pack_start(self._btn_editor, False, False, 0)

        self._btn_preview = Gtk.RadioButton.new_with_label_from_widget(self._btn_split, "👁️ Preview")
        self._btn_preview.set_mode(False)
        self._btn_preview.get_style_context().add_class("btn-mode")
        self._btn_preview.connect("toggled", lambda b: self._on_mode_toggled(b, self.MODE_PREVIEW))
        mode_box.pack_start(self._btn_preview, False, False, 0)

        toolbar_box.pack_start(mode_box, False, False, 0)

        # Grupo de Acessibilidade: Ajuste de Tamanho da Fonte (A- / 14px / A+)
        font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        font_box.get_style_context().add_class("font-size-box")

        self._btn_font_dec = Gtk.Button(label="A-")
        self._btn_font_dec.get_style_context().add_class("btn-font-size")
        self._btn_font_dec.set_tooltip_text("Reduzir Tamanho da Fonte (Ctrl+-)")
        self._btn_font_dec.connect("clicked", lambda _: self.decrease_font_size())
        font_box.pack_start(self._btn_font_dec, False, False, 0)

        self._lbl_font_size = Gtk.Label(label=f"{self._font_size}px")
        self._lbl_font_size.get_style_context().add_class("lbl-font-indicator")
        self._lbl_font_size.set_tooltip_text("Tamanho Atual da Fonte (Clique para restaurar padrão)")

        font_event_box = Gtk.EventBox()
        font_event_box.add(self._lbl_font_size)
        font_event_box.connect("button-press-event", lambda _w, _e: self.reset_font_size())
        font_box.pack_start(font_event_box, False, False, 0)

        self._btn_font_inc = Gtk.Button(label="A+")
        self._btn_font_inc.get_style_context().add_class("btn-font-size")
        self._btn_font_inc.set_tooltip_text("Aumentar Tamanho da Fonte (Ctrl++)")
        self._btn_font_inc.connect("clicked", lambda _: self.increase_font_size())
        font_box.pack_start(self._btn_font_inc, False, False, 0)

        toolbar_box.pack_start(font_box, False, False, 0)

        # Botão Salvar (Ctrl+S)
        self._btn_save = Gtk.Button(label="💾 Salvar")
        self._btn_save.get_style_context().add_class("btn-primary")
        self._btn_save.set_tooltip_text("Salvar Nota (Ctrl+S)")
        self._btn_save.connect("clicked", lambda _: self._trigger_save())
        toolbar_box.pack_end(self._btn_save, False, False, 0)

        self.pack_start(toolbar_box, False, False, 0)

        # 2. Container de Conteúdo Dividido (Paned)
        self._paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self._paned.set_position(450)
        self.pack_start(self._paned, True, True, 0)

        # Painel Esquerdo: Área de Edição
        self._editor_scrolled = Gtk.ScrolledWindow()
        self._editor_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._editor_text_view = Gtk.TextView()
        self._editor_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._editor_text_view.get_style_context().add_class("editor-textview")
        self._editor_text_view.connect("key-press-event", self._on_key_press_event)
        
        self._editor_buffer = self._editor_text_view.get_buffer()
        self._editor_buffer.connect("changed", self._on_text_changed)
        self._editor_buffer.connect("mark-set", self._on_mark_set)
        self._editor_scrolled.add(self._editor_text_view)

        # Painel Direito: Live Preview Renderizado
        self._preview_scrolled = Gtk.ScrolledWindow()
        self._preview_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._preview_text_view = Gtk.TextView()
        self._preview_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._preview_text_view.set_editable(False)
        self._preview_text_view.set_cursor_visible(False)
        self._preview_text_view.get_style_context().add_class("preview-textview")
        self._preview_text_view.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self._preview_text_view.connect("motion-notify-event", self._on_preview_motion_notify)
        self._preview_text_view.connect("button-release-event", self._on_preview_button_release)

        self._preview_buffer = self._preview_text_view.get_buffer()
        self._preview_scrolled.add(self._preview_text_view)

        self._paned.pack1(self._editor_scrolled, resize=True, shrink=False)
        self._paned.pack2(self._preview_scrolled, resize=True, shrink=False)

        # 3. Barra Inferior de Navegação do Editor (Linha, Coluna e Estatísticas)
        self._footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._footer_box.get_style_context().add_class("editor-footer-bar")

        self._lbl_cursor_pos = Gtk.Label(label="Linha 1, Coluna 1")
        self._lbl_cursor_pos.set_xalign(0.0)
        self._lbl_cursor_pos.get_style_context().add_class("editor-pos-label")
        self._footer_box.pack_start(self._lbl_cursor_pos, False, False, 0)

        self._lbl_stats = Gtk.Label(label="0 palavras • 0 caracteres")
        self._lbl_stats.set_xalign(0.0)
        self._lbl_stats.get_style_context().add_class("editor-stats-label")
        self._footer_box.pack_start(self._lbl_stats, False, False, 0)

        self.pack_end(self._footer_box, False, False, 0)

    def _on_mark_set(self, buffer: Gtk.TextBuffer, iter_: Gtk.TextIter, mark: Gtk.TextMark) -> None:
        """Atualiza a informação de linha e coluna quando o cursor se move."""
        if mark.get_name() == "insert":
            line = iter_.get_line() + 1
            col = iter_.get_line_offset() + 1
            self._lbl_cursor_pos.set_label(f"Linha {line}, Coluna {col}")

    def _update_stats(self) -> None:
        """Atualiza a contagem de palavras e caracteres."""
        content = self.get_content()
        char_count = len(content)
        word_count = len(content.split()) if content.strip() else 0
        self._lbl_stats.set_label(f"{word_count} palavras • {char_count} caracteres")

    def _on_key_press_event(self, widget: object, event: object) -> bool:
        """Captura os atalhos de teclado (Ctrl+S, Ctrl+Z, Ctrl+Shift+Z, Ctrl+Y, Ctrl+A, Ctrl+C, Ctrl+X, Ctrl+V)."""
        is_ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        is_shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
        key = event.keyval

        if is_ctrl:
            # 1. Salvar (Ctrl+S)
            if key in (Gdk.KEY_s, Gdk.KEY_S):
                self._trigger_save()
                return True

            # 2. Desfazer (Ctrl+Z sem Shift)
            if not is_shift and key in (Gdk.KEY_z, Gdk.KEY_Z):
                self._undo()
                return True

            # 3. Refazer (Ctrl+Shift+Z ou Ctrl+Y)
            if (is_shift and key in (Gdk.KEY_z, Gdk.KEY_Z)) or key in (Gdk.KEY_y, Gdk.KEY_Y):
                self._redo()
                return True

            # 4. Selecionar Tudo (Ctrl+A)
            if key in (Gdk.KEY_a, Gdk.KEY_A):
                if widget == self._editor_text_view:
                    self._select_all()
                    return True

            # 5. Copiar (Ctrl+C)
            if key in (Gdk.KEY_c, Gdk.KEY_C):
                if widget == self._editor_text_view:
                    self._copy()
                    return True

            # 6. Recortar (Ctrl+X)
            if key in (Gdk.KEY_x, Gdk.KEY_X):
                if widget == self._editor_text_view:
                    self._cut()
                    return True

            # 7. Colar (Ctrl+V)
            if key in (Gdk.KEY_v, Gdk.KEY_V):
                if widget == self._editor_text_view:
                    self._paste()
                    return True

            # 8. Acessibilidade: Aumentar Fonte (Ctrl + + / Ctrl + =)
            if key in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
                self.increase_font_size()
                return True

            # 9. Acessibilidade: Reduzir Fonte (Ctrl + - / Ctrl + _)
            if key in (Gdk.KEY_minus, Gdk.KEY_underscore, Gdk.KEY_KP_Subtract):
                self.decrease_font_size()
                return True

            # 10. Acessibilidade: Restaurar Tamanho Padrão (Ctrl + 0)
            if key in (Gdk.KEY_0, Gdk.KEY_KP_0):
                self.reset_font_size()
                return True

        return False

    def _push_undo_state(self, content: str) -> None:
        """Registra o estado atual na pilha de Undo se houver modificação."""
        if not self._undo_stack or self._undo_stack[-1] != content:
            self._undo_stack.append(content)
            if len(self._undo_stack) > 100:
                self._undo_stack.pop(0)
            self._redo_stack.clear()

    def _undo(self) -> None:
        """Desfaz a última alteração de texto."""
        if len(self._undo_stack) > 1:
            current_state = self._undo_stack.pop()
            self._redo_stack.append(current_state)
            previous_state = self._undo_stack[-1]

            self._is_updating_programmatically = True
            try:
                self._editor_buffer.set_text(previous_state)
            finally:
                self._is_updating_programmatically = False

            self._update_preview()
            self._update_stats()

    def _redo(self) -> None:
        """Refaz a última alteração desfeita."""
        if self._redo_stack:
            next_state = self._redo_stack.pop()
            self._undo_stack.append(next_state)

            self._is_updating_programmatically = True
            try:
                self._editor_buffer.set_text(next_state)
            finally:
                self._is_updating_programmatically = False

            self._update_preview()
            self._update_stats()

    def _select_all(self) -> None:
        """Seleciona todo o texto do buffer."""
        start_iter = self._editor_buffer.get_start_iter()
        end_iter = self._editor_buffer.get_end_iter()
        self._editor_buffer.select_range(start_iter, end_iter)

    def _copy(self) -> None:
        """Copia a seleção para a área de transferência."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._editor_buffer.copy_clipboard(clipboard)

    def _cut(self) -> None:
        """Recorta a seleção para a área de transferência."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._editor_buffer.cut_clipboard(clipboard, True)

    def _paste(self) -> None:
        """Cola o conteúdo da área de transferência na posição do cursor."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._editor_buffer.paste_clipboard(clipboard, None, True)

    def _trigger_save(self) -> None:
        """Dispara o callback de salvamento com título e conteúdo atuais."""
        if self.on_save_requested:
            title = self.get_title()
            content = self.get_content()
            self.on_save_requested(title, content)

    def _on_text_changed(self, widget: object) -> None:
        """Manipula alteração no texto disparando o debounce de renderização do preview."""
        if self._is_updating_programmatically:
            return

        current_content = self.get_content()
        self._push_undo_state(current_content)
        self._update_stats()

        if self._debounce_timer_id is not None:
            GLib.source_remove(self._debounce_timer_id)

        self._debounce_timer_id = GLib.timeout_add(120, self._update_preview)

        if self.on_content_changed:
            self.on_content_changed(self.get_title(), self.get_content())

    def _update_preview(self) -> bool:
        """Renderiza o conteúdo do editor com imagens, links clicáveis e âncoras de footnotes."""
        self._debounce_timer_id = None
        content = self.get_content()
        is_dark = default_config.theme == "dark"
        colors = ThemeColors.for_theme(is_dark)

        try:
            self._preview_buffer.set_text("")
            raw_pango = self.markdown_service.render_to_pango(content, is_dark=is_dark)

            # Insere todo o Pango Markup de uma só vez (garantindo XML válido e balanceado)
            end_iter = self._preview_buffer.get_end_iter()
            self._preview_buffer.insert_markup(end_iter, raw_pango, -1)

            # Enriquece o buffer com interatividade (links clicáveis, âncoras e imagens locais)
            self._enrich_preview_interactivity(content, colors)

        except Exception as e:
            logger.debug(f"Pango Markup render fallback: {e}")
            self._preview_buffer.set_text(content)

        return False

    def _enrich_preview_interactivity(self, raw_markdown: str, colors: ThemeColors) -> None:
        """Enriquece o buffer pós-renderização com tags interativas para links, footnotes e imagens."""
        start_iter = self._preview_buffer.get_start_iter()
        end_iter = self._preview_buffer.get_end_iter()
        buf_text = self._preview_buffer.get_text(start_iter, end_iter, True)
        if not buf_text:
            return

        # 1. Definições de Footnote [^id]:
        for fn_def_match in re.finditer(r"\[\^([a-zA-Z0-9_\-]+)\]:", buf_text):
            fn_id = fn_def_match.group(1)
            iter_start = self._preview_buffer.get_iter_at_offset(fn_def_match.start())
            iter_end = self._preview_buffer.get_iter_at_offset(fn_def_match.end())

            self._preview_buffer.create_mark(f"fn_def_{fn_id}", iter_start, True)
            def_tag = self._preview_buffer.create_tag(None)
            def_tag.footnote_target = f"fn_ref_{fn_id}"
            self._preview_buffer.apply_tag(def_tag, iter_start, iter_end)

        # 2. Referências de Footnote [id]
        for fn_ref_match in re.finditer(r"\[([a-zA-Z0-9_\-]+)\]", buf_text):
            fn_id = fn_ref_match.group(1)
            iter_start = self._preview_buffer.get_iter_at_offset(fn_ref_match.start())
            iter_end = self._preview_buffer.get_iter_at_offset(fn_ref_match.end())

            self._preview_buffer.create_mark(f"fn_ref_{fn_id}", iter_start, True)
            ref_tag = self._preview_buffer.create_tag(None)
            ref_tag.footnote_target = f"fn_def_{fn_id}"
            self._preview_buffer.apply_tag(ref_tag, iter_start, iter_end)

        # 3. Links Markdown [Texto](url) da nota original
        for link_match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", raw_markdown):
            label, url = link_match.group(1), link_match.group(2)
            # Procura a ocorrência de `label` no buffer
            idx = 0
            while True:
                pos = buf_text.find(label, idx)
                if pos == -1:
                    break
                iter_start = self._preview_buffer.get_iter_at_offset(pos)
                iter_end = self._preview_buffer.get_iter_at_offset(pos + len(label))
                tag = self._preview_buffer.create_tag(None)
                tag.url = url
                self._preview_buffer.apply_tag(tag, iter_start, iter_end)
                idx = pos + len(label)

        # 4. Autolinks e URLs puras (https://... / http://... / mailto:...)
        for url_match in re.finditer(r"(https?://[^\s<>\"'()]+|mailto:[^\s<>\"'()]+)", buf_text):
            url = url_match.group(1)
            iter_start = self._preview_buffer.get_iter_at_offset(url_match.start())
            iter_end = self._preview_buffer.get_iter_at_offset(url_match.end())
            tag = self._preview_buffer.create_tag(None)
            tag.url = url
            self._preview_buffer.apply_tag(tag, iter_start, iter_end)

        # 5. Imagens locais ![alt](caminho)
        for img_match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", raw_markdown):
            alt, src = img_match.group(1), img_match.group(2)
            # Procura o placeholder da imagem no buffer
            needle = f"🖼️ [Imagem: {alt}]"
            pos = buf_text.find(needle)
            if pos != -1:
                # Tenta carregar imagem local se existir
                resolved_path = self._resolve_local_image_path(src)
                if resolved_path:
                    try:
                        iter_start = self._preview_buffer.get_iter_at_offset(pos)
                        iter_end = self._preview_buffer.get_iter_at_offset(pos + len(needle))
                        self._preview_buffer.delete(iter_start, iter_end)
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(resolved_path), 480, 320, True)
                        insert_iter = self._preview_buffer.get_iter_at_offset(pos)
                        img_tag = self._preview_buffer.create_tag(None)
                        img_tag.image_path = str(resolved_path)
                        img_tag.image_title = alt or resolved_path.name
                        self._preview_buffer.insert_pixbuf(insert_iter, pixbuf)
                        tag_start = self._preview_buffer.get_iter_at_offset(pos)
                        tag_end = self._preview_buffer.get_iter_at_offset(pos + 1)
                        self._preview_buffer.apply_tag(img_tag, tag_start, tag_end)
                        self._preview_buffer.insert(self._preview_buffer.get_iter_at_offset(pos + 1), "\n")
                        # Atualiza buf_text para buscas subsequentes
                        buf_text = self._preview_buffer.get_text(
                            self._preview_buffer.get_start_iter(),
                            self._preview_buffer.get_end_iter(),
                            True,
                        )
                    except Exception as e:
                        logger.warning(f"Falha ao renderizar imagem local {resolved_path}: {e}")

        # 6. Diagramas Mermaid 🖼️ [Mermaid: caminho_svg]
        for mermaid_match in re.finditer(r"🖼️ \[Mermaid: ([^\]]+)\]", buf_text):
            svg_src = mermaid_match.group(1).strip()
            placeholder_text = mermaid_match.group(0)
            svg_path = Path(svg_src)
            if svg_path.exists() and svg_path.is_file():
                try:
                    pos = buf_text.find(placeholder_text)
                    if pos != -1:
                        iter_start = self._preview_buffer.get_iter_at_offset(pos)
                        iter_end = self._preview_buffer.get_iter_at_offset(pos + len(placeholder_text))
                        self._preview_buffer.delete(iter_start, iter_end)
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(svg_path), 800, 600, True)
                        insert_iter = self._preview_buffer.get_iter_at_offset(pos)
                        diag_tag = self._preview_buffer.create_tag(None)
                        diag_tag.image_path = str(svg_path)
                        diag_tag.image_title = "Diagrama Mermaid"
                        self._preview_buffer.insert_pixbuf(insert_iter, pixbuf)
                        tag_start = self._preview_buffer.get_iter_at_offset(pos)
                        tag_end = self._preview_buffer.get_iter_at_offset(pos + 1)
                        self._preview_buffer.apply_tag(diag_tag, tag_start, tag_end)
                        self._preview_buffer.insert(self._preview_buffer.get_iter_at_offset(pos + 1), "\n")
                        buf_text = self._preview_buffer.get_text(
                            self._preview_buffer.get_start_iter(),
                            self._preview_buffer.get_end_iter(),
                            True,
                        )
                except Exception as e:
                    logger.warning(f"Falha ao renderizar diagrama Mermaid {svg_path}: {e}")

    def _resolve_local_image_path(self, src: str) -> Optional[Path]:
        """Resolve o caminho de um arquivo de imagem local considerando múltiplos diretórios candidatos.

        Ordem de resolução:
        1. Caminho absoluto direto no sistema de arquivos.
        2. Relativo ao diretório da nota ativa (e subdiretórios comuns de anexos).
        3. Relativo à raiz do workspace ativo (e subdiretórios comuns de anexos).
        """
        clean_src = urllib.parse.unquote(src).strip()
        if not clean_src or clean_src.startswith(("http://", "https://", "data:")):
            return None

        # Lista de subdiretórios padrão de anexos e mídias
        asset_subdirs = ["", "assets", "attachments", "images", "img", "media"]

        # 1. Caminho absoluto
        candidate = Path(clean_src)
        if candidate.is_absolute() and candidate.exists() and candidate.is_file():
            return candidate

        # 2. Relativo à pasta da nota ativa
        if self._current_note_path:
            note_dir = Path(self._current_note_path).parent.resolve()
            for subdir in asset_subdirs:
                target = (note_dir / subdir / clean_src).resolve() if subdir else (note_dir / clean_src).resolve()
                if target.exists() and target.is_file():
                    return target

        # 3. Relativo à raiz do workspace ativo
        if default_config.active_vault_path:
            vault_root = Path(default_config.active_vault_path).resolve()
            for subdir in asset_subdirs:
                target = (vault_root / subdir / clean_src).resolve() if subdir else (vault_root / clean_src).resolve()
                if target.exists() and target.is_file():
                    return target

        return None

    def _get_iter_from_location(self, x: int, y: int) -> Optional[object]:
        """Obtém o TextIter nas coordenadas do buffer compatível com tupla PyGObject."""
        res = self._preview_text_view.get_iter_at_location(x, y)
        if hasattr(res, "iter"):
            return res.iter
        if isinstance(res, (tuple, list)) and len(res) > 1:
            return res[1]
        return res if res else None

    def _on_preview_motion_notify(self, widget: object, event: object) -> bool:
        """Altera o cursor para ponteiro quando o mouse passa sobre links, footnotes ou imagens."""
        x, y = self._preview_text_view.window_to_buffer_coords(Gtk.TextWindowType.TEXT, int(event.x), int(event.y))
        iter_ = self._get_iter_from_location(x, y)
        is_interactive = False

        if iter_ and hasattr(iter_, "get_tags"):
            tags = iter_.get_tags()
            for tag in tags:
                if (
                    getattr(tag, "url", None)
                    or getattr(tag, "footnote_target", None)
                    or getattr(tag, "image_path", None)
                ):
                    is_interactive = True
                    break

        window = self._preview_text_view.get_window(Gtk.TextWindowType.TEXT)
        if window:
            display = self.get_display() if hasattr(self, "get_display") else Gdk.Display.get_default()
            cursor = Gdk.Cursor.new_from_name(display, "pointer") if is_interactive else None
            window.set_cursor(cursor)

        return False

    def _on_preview_button_release(self, widget: object, event: object) -> bool:
        """Abre links no navegador, rola até footnotes ou abre imagens no lightbox ao clicar."""
        if event.button == 1:
            x, y = self._preview_text_view.window_to_buffer_coords(Gtk.TextWindowType.TEXT, int(event.x), int(event.y))
            iter_ = self._get_iter_from_location(x, y)
            if iter_ and hasattr(iter_, "get_tags"):
                tags = iter_.get_tags()
                for tag in tags:
                    # 1. Clique em Imagem ou Diagrama -> Abre Lightbox
                    image_path = getattr(tag, "image_path", None)
                    if image_path:
                        try:
                            from src.views.components.image_lightbox import ImageLightboxDialog
                            toplevel = self.get_toplevel() if hasattr(self, "get_toplevel") else None
                            dlg = ImageLightboxDialog(
                                parent=toplevel,
                                image_path=image_path,
                                title=getattr(tag, "image_title", None),
                            )
                            return True
                        except Exception as e:
                            logger.error(f"Erro ao abrir lightbox de imagem: {e}")

                    # 2. Clique em Link Web -> Abre Navegador
                    url = getattr(tag, "url", None)
                    if url and url.startswith(("http://", "https://", "mailto:")):
                        webbrowser.open_new_tab(url)
                        return True

                    # 3. Clique em Âncora de Footnote -> Rola até a marca
                    fn_target = getattr(tag, "footnote_target", None)
                    if fn_target:
                        mark = self._preview_buffer.get_mark(fn_target)
                        if mark:
                            self._preview_text_view.scroll_to_mark(mark, 0.05, True, 0.0, 0.1)
                            return True

        return False

    def _on_mode_toggled(self, button: Gtk.RadioButton, mode: str) -> None:
        """Alterna a visibilidade dos painéis de acordo com o modo selecionado."""
        if button.get_active():
            self.set_view_mode(mode)

    def set_view_mode(self, mode: str) -> None:
        """Define o modo de visualização ('split', 'editor', 'preview')."""
        self._current_mode = mode

        if mode == self.MODE_SPLIT:
            self._editor_scrolled.set_visible(True)
            self._preview_scrolled.set_visible(True)
            self._paned.set_position(self.get_allocated_width() // 2 or 450)
            self._btn_split.set_active(True)
        elif mode == self.MODE_EDITOR:
            self._editor_scrolled.set_visible(True)
            self._preview_scrolled.set_visible(False)
            self._btn_editor.set_active(True)
        elif mode == self.MODE_PREVIEW:
            self._editor_scrolled.set_visible(False)
            self._preview_scrolled.set_visible(True)
            self._update_preview()
            self._btn_preview.set_active(True)

    def refresh_preview(self) -> None:
        """Método público para forçar a atualização do Live Preview.

        Substitui o acesso direto a _update_preview() que era usado
        pela MainWindow (violação de encapsulamento).
        """
        self._update_preview()

    def set_note(self, title: str, content: str, note_path: Optional[str] = None) -> None:
        """Carrega uma nova nota no editor e atualiza o preview imediatamente.

        :param title: Título da nota
        :param content: Conteúdo Markdown da nota
        :param note_path: Caminho completo do arquivo no disco (para resolução de anexos locais)
        """
        self._current_note_path = note_path
        if not GTK_AVAILABLE:
            self._raw_title = title
            self._raw_content = content
            return

        self._is_updating_programmatically = True
        try:
            self._title_entry.set_text(title)
            self._editor_buffer.set_text(content)
            self._undo_stack = [content]
            self._redo_stack.clear()
        finally:
            self._is_updating_programmatically = False

        self._update_preview()
        self._update_stats()

    def get_title(self) -> str:
        """Retorna o título atual do editor."""
        if not GTK_AVAILABLE:
            return self._raw_title
        return self._title_entry.get_text().strip()

    def get_content(self) -> str:
        """Retorna o conteúdo Markdown bruto do editor."""
        if not GTK_AVAILABLE:
            return self._raw_content
        start_iter, end_iter = self._editor_buffer.get_bounds()
        return self._editor_buffer.get_text(start_iter, end_iter, True)

    def clear(self) -> None:
        """Limpa o editor e a visualização."""
        self._current_note_path = None
        if not GTK_AVAILABLE:
            self._raw_title = ""
            self._raw_content = ""
            return

        self._is_updating_programmatically = True
        try:
            self._title_entry.set_text("")
            self._editor_buffer.set_text("")
            self._preview_buffer.set_text("")
            self._undo_stack.clear()
            self._redo_stack.clear()
        finally:
            self._is_updating_programmatically = False
        self._update_stats()

    # --- Métodos de Acessibilidade / Controle de Fonte ---

    def get_font_size(self) -> int:
        """Retorna o tamanho atual da fonte em pixels."""
        return getattr(self, "_font_size", default_config.font_size)

    def apply_font_size(self, size: int) -> int:
        """Aplica o tamanho de fonte especificado nos TextViews e atualiza o indicador visual."""
        from src.core.config import MIN_FONT_SIZE, MAX_FONT_SIZE
        clamped_size = max(MIN_FONT_SIZE, min(size, MAX_FONT_SIZE))
        self._font_size = clamped_size
        default_config.font_size = clamped_size

        if GTK_AVAILABLE:
            if hasattr(self, "_lbl_font_size") and self._lbl_font_size:
                self._lbl_font_size.set_text(f"{clamped_size}px")

            css_data = f"""
            .editor-textview {{ font-size: {clamped_size}px; }}
            .preview-textview {{ font-size: {clamped_size}px; }}
            """.encode("utf-8")

            if self._font_css_provider is None:
                self._font_css_provider = Gtk.CssProvider()
                screen = Gdk.Screen.get_default()
                if screen:
                    Gtk.StyleContext.add_provider_for_screen(
                        screen,
                        self._font_css_provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10,
                    )

            try:
                self._font_css_provider.load_from_data(css_data)
            except Exception as e:
                logger.debug(f"Erro ao carregar CSS dinâmico de fonte: {e}")

        return clamped_size

    def increase_font_size(self) -> int:
        """Aumenta o tamanho da fonte em 2px até o limite máximo de 32px."""
        from src.core.config import FONT_SIZE_STEP
        return self.apply_font_size(self.get_font_size() + FONT_SIZE_STEP)

    def decrease_font_size(self) -> int:
        """Diminui o tamanho da fonte em 2px até o limite mínimo de 10px."""
        from src.core.config import FONT_SIZE_STEP
        return self.apply_font_size(self.get_font_size() - FONT_SIZE_STEP)

    def reset_font_size(self) -> int:
        """Restaura o tamanho padrão da fonte (14px)."""
        from src.core.config import DEFAULT_FONT_SIZE
        return self.apply_font_size(DEFAULT_FONT_SIZE)

