"""Janela principal da aplicação MarkAtlas (GTK Application Window)."""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path
from typing import Optional
from src.core.config import AppConfig, default_config
from src.core.style_manager import StyleManager
from src.controllers.workspace_controller import WorkspaceController
from src.views.components.workspace_tree import WorkspaceTreeView
from src.views.components.markdown_editor import MarkdownEditorView
from src.views.dialogs.prompt_dialog import show_confirm_dialog, show_prompt_dialog

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, Gio, GLib
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    Gtk = object  # type: ignore


class MainWindow(Gtk.ApplicationWindow if GTK_AVAILABLE else object):  # type: ignore
    """Janela principal do MarkAtlas com menus, navegação em árvore e editor integrado com live preview."""

    def __init__(
        self,
        app: Optional[object] = None,
        title: str = "MarkAtlas",
        controller: Optional[WorkspaceController] = None,
    ) -> None:
        if not GTK_AVAILABLE:
            logger.warning("PyGObject / GTK 3.0 não está disponível no ambiente atual.")
            self.title = title
            return

        super().__init__(application=app, title=title)
        self.set_default_size(1220, 780)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class("main-window")

        self.controller = controller or WorkspaceController()
        self._lbl_vault: Optional[Gtk.Label] = None
        self._tree_view: Optional[WorkspaceTreeView] = None
        self._editor_view: Optional[MarkdownEditorView] = None
        self._lbl_status: Optional[Gtk.Label] = None
        self._sidebar_box: Optional[Gtk.Box] = None

        self._build_ui()
        self._setup_initial_workspace()
        self.connect("key-press-event", self._on_main_key_press_event)

    def _build_ui(self) -> None:
        """Constrói a interface com menus, HeaderBar, Sidebar e Editor Live Preview."""
        # 1. HeaderBar
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("MarkAtlas")
        header_bar.set_subtitle("Gestão de Conhecimento em Markdown")
        header_bar.get_style_context().add_class("header-bar")
        self.set_titlebar(header_bar)

        # Layout Vertical Principal (MenuBar + Conteúdo)
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_vbox)

        # 2. Barra de Menus e Submenus
        menu_bar = self._create_menu_bar()
        root_vbox.pack_start(menu_bar, False, False, 0)

        # 3. Container Principal Dividido (Sidebar / Editor)
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_position(280)
        root_vbox.pack_start(main_paned, True, True, 0)

        # 4. Sidebar (Esquerda)
        self._sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._sidebar_box.get_style_context().add_class("sidebar-container")

        # Cabeçalho da Sidebar (Nome do Workspace e Ações Rápidas)
        vault_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        vault_header_box.get_style_context().add_class("sidebar-header")

        self._lbl_vault = Gtk.Label(label="📁 Nenhum Workspace")
        self._lbl_vault.set_xalign(0.0)
        self._lbl_vault.get_style_context().add_class("vault-title")
        vault_header_box.pack_start(self._lbl_vault, True, True, 2)

        # Botão rápido para Nova Nota na raiz
        btn_add_note = Gtk.Button(label="+")
        btn_add_note.get_style_context().add_class("btn-icon")
        btn_add_note.set_tooltip_text("Criar Nova Nota no Workspace")
        btn_add_note.connect("clicked", lambda _: self._on_new_note_clicked(None))
        vault_header_box.pack_end(btn_add_note, False, False, 0)

        # Botão rápido para Nova Pasta na raiz
        btn_add_folder = Gtk.Button(label="📁+")
        btn_add_folder.get_style_context().add_class("btn-icon")
        btn_add_folder.set_tooltip_text("Criar Nova Pasta no Workspace")
        btn_add_folder.connect("clicked", self._on_create_root_folder_clicked)
        vault_header_box.pack_end(btn_add_folder, False, False, 0)

        self._sidebar_box.pack_start(vault_header_box, False, False, 2)

        # Árvore de Arquivos, Sub-árvore de Tags e Menus Contextuais
        self._tree_view = WorkspaceTreeView(
            on_file_selected=self._on_file_selected,
            on_tag_selected=self._on_tag_selected,
            on_delete_file_requested=self._on_delete_file_requested,
            on_create_file_in_folder_requested=self._on_create_file_in_folder_requested,
            on_create_folder_requested=self._on_create_folder_requested,
            on_delete_folder_requested=self._on_delete_folder_requested,
            on_rename_file_requested=self._on_rename_file_requested,
            on_rename_folder_requested=self._on_rename_folder_requested,
        )
        self._sidebar_box.pack_start(self._tree_view, True, True, 0)

        main_paned.pack1(self._sidebar_box, resize=False, shrink=False)

        # 5. Área do Editor e Live Preview (Direita)
        right_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._editor_view = MarkdownEditorView(
            on_save_requested=self._on_editor_save_requested,
            on_content_changed=self._on_editor_content_changed,
        )
        right_container.pack_start(self._editor_view, True, True, 0)

        # Barra de Status
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_bar.get_style_context().add_class("status-bar")
        self._lbl_status = Gtk.Label(label="MarkAtlas v0.1.0 • Pronto")
        self._lbl_status.set_xalign(0.0)
        status_bar.pack_start(self._lbl_status, True, True, 0)
        right_container.pack_end(status_bar, False, False, 0)

        main_paned.pack2(right_container, resize=True, shrink=False)

    def _create_menu_bar(self) -> Gtk.MenuBar:
        """Cria a barra de menus e submenus principais da aplicação."""
        menu_bar = Gtk.MenuBar()
        menu_bar.get_style_context().add_class("app-menu-bar")

        # --- Menu Arquivo ---
        item_file = Gtk.MenuItem(label="Arquivo")
        sub_file = Gtk.Menu()
        item_file.set_submenu(sub_file)

        mi_open = Gtk.MenuItem(label="Abrir Workspace / Cofre...")
        mi_open.connect("activate", self._on_open_workspace_dialog)
        sub_file.append(mi_open)

        mi_new = Gtk.MenuItem(label="Nova Nota (Ctrl+N)")
        mi_new.connect("activate", self._on_new_note_clicked)
        sub_file.append(mi_new)

        mi_refresh = Gtk.MenuItem(label="Recarregar Workspace (F5)")
        mi_refresh.connect("activate", self._on_refresh_workspace)
        sub_file.append(mi_refresh)

        sub_file.append(Gtk.SeparatorMenuItem())

        mi_quit = Gtk.MenuItem(label="Sair")
        mi_quit.connect("activate", lambda _: self.close())
        sub_file.append(mi_quit)

        menu_bar.append(item_file)

        # --- Menu Editar ---
        item_edit = Gtk.MenuItem(label="Editar")
        sub_edit = Gtk.Menu()
        item_edit.set_submenu(sub_edit)

        mi_save = Gtk.MenuItem(label="Salvar Nota (Ctrl+S)")
        mi_save.connect("activate", self._on_save_note_clicked)
        sub_edit.append(mi_save)

        menu_bar.append(item_edit)

        # --- Menu Exibir ---
        item_view = Gtk.MenuItem(label="Exibir")
        sub_view = Gtk.Menu()
        item_view.set_submenu(sub_view)

        mi_mode_split = Gtk.MenuItem(label="Modo Lado a Lado (Split)")
        mi_mode_split.connect("activate", lambda _: self._editor_view and self._editor_view.set_view_mode("split"))
        sub_view.append(mi_mode_split)

        mi_mode_editor = Gtk.MenuItem(label="Modo Só Editor")
        mi_mode_editor.connect("activate", lambda _: self._editor_view and self._editor_view.set_view_mode("editor"))
        sub_view.append(mi_mode_editor)

        mi_mode_preview = Gtk.MenuItem(label="Modo Só Preview")
        mi_mode_preview.connect("activate", lambda _: self._editor_view and self._editor_view.set_view_mode("preview"))
        sub_view.append(mi_mode_preview)

        sub_view.append(Gtk.SeparatorMenuItem())

        mi_theme = Gtk.MenuItem(label="Alternar Tema (Claro / Escuro)")
        mi_theme.connect("activate", self._on_toggle_theme)
        sub_view.append(mi_theme)

        mi_sidebar = Gtk.MenuItem(label="Alternar Barra Lateral")
        mi_sidebar.connect("activate", self._on_toggle_sidebar)
        sub_view.append(mi_sidebar)

        sub_view.append(Gtk.SeparatorMenuItem())

        # Acessibilidade: Controle de Tamanho da Fonte
        mi_font_inc = Gtk.MenuItem(label="🔍 Aumentar Fonte (Ctrl++)")
        mi_font_inc.connect("activate", lambda _: self._on_increase_font())
        sub_view.append(mi_font_inc)

        mi_font_dec = Gtk.MenuItem(label="🔍 Reduzir Fonte (Ctrl+-)")
        mi_font_dec.connect("activate", lambda _: self._on_decrease_font())
        sub_view.append(mi_font_dec)

        mi_font_reset = Gtk.MenuItem(label="Restaurar Tamanho Padrão (Ctrl+0)")
        mi_font_reset.connect("activate", lambda _: self._on_reset_font())
        sub_view.append(mi_font_reset)

        menu_bar.append(item_view)

        # --- Menu Ajuda ---
        item_help = Gtk.MenuItem(label="Ajuda")
        sub_help = Gtk.Menu()
        item_help.set_submenu(sub_help)

        mi_md_basic = Gtk.MenuItem(label="📖 Sintaxe Básica do Markdown...")
        mi_md_basic.connect("activate", lambda _: self._open_url("https://www.markdownguide.org/basic-syntax/"))
        sub_help.append(mi_md_basic)

        mi_md_ext = Gtk.MenuItem(label="🚀 Sintaxe Estendida do Markdown...")
        mi_md_ext.connect("activate", lambda _: self._open_url("https://www.markdownguide.org/extended-syntax/"))
        sub_help.append(mi_md_ext)

        mi_md_guide = Gtk.MenuItem(label="🌐 Guia Completo (Markdown Guide)...")
        mi_md_guide.connect("activate", lambda _: self._open_url("https://www.markdownguide.org/"))
        sub_help.append(mi_md_guide)

        sub_help.append(Gtk.SeparatorMenuItem())

        mi_about = Gtk.MenuItem(label="Sobre o MarkAtlas")
        mi_about.connect("activate", self._on_show_about)
        sub_help.append(mi_about)

        menu_bar.append(item_help)

        return menu_bar

    def _setup_initial_workspace(self) -> None:
        """Carrega o workspace inicial se houver cofre configurado."""
        active_path = default_config.active_vault_path
        if active_path and Path(active_path).exists():
            self._load_workspace(active_path)

    def _load_workspace(self, folder_path: str) -> None:
        """Abre a pasta no controller e atualiza a árvore e labels."""
        try:
            vault = self.controller.open_workspace(folder_path)
            if self._lbl_vault:
                self._lbl_vault.set_label(f"📁 {vault.name}")

            tree_data = self.controller.get_workspace_tree()
            if self._tree_view:
                self._tree_view.populate(tree_data, root_path=folder_path)

            if self._lbl_status:
                self._lbl_status.set_label(f"Workspace carregado: {vault.name} • {vault.total_notes} notas encontradas")
        except Exception as e:
            logger.error(f"Erro ao carregar workspace {folder_path}: {e}")
            if self._lbl_status:
                self._lbl_status.set_label(f"Erro ao abrir workspace: {e}")

    def _on_open_workspace_dialog(self, _widget: object) -> None:
        """Exibe o diálogo nativo para seleção de pasta do workspace."""
        dialog = Gtk.FileChooserDialog(
            title="Selecionar Pasta do Workspace / Cofre",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            dialog.destroy()
            if folder:
                self._load_workspace(folder)
        else:
            dialog.destroy()

    def _on_file_selected(self, file_path: str) -> None:
        """Manipula a seleção de um arquivo Markdown na árvore."""
        note = self.controller.load_note(file_path)
        if not note:
            return

        if self._editor_view:
            self._editor_view.set_note(note.title, note.content, note_path=note.path)

        # Gera e expande a sub-árvore de tags sob este arquivo
        if self._tree_view:
            self._tree_view.update_tags_for_file(file_path, note.tags)

        # Atualiza o status
        if self._lbl_status:
            tags_info = f"{len(note.tags)} tags" if note.tags else "sem tags"
            self._lbl_status.set_label(f"📄 {Path(file_path).name} • {note.word_count} palavras • {tags_info}")

    def _on_tag_selected(self, tag_name: str, file_path: str) -> None:
        """Manipula a seleção de uma tag na sub-árvore."""
        if self._lbl_status:
            file_name = Path(file_path).name if file_path else ""
            self._lbl_status.set_label(f"🏷️ Tag selecionada: #{tag_name} (em {file_name})")

    def _on_save_note_clicked(self, _widget: object) -> None:
        """Salva a nota ativa a partir do menu."""
        if self._editor_view:
            title = self._editor_view.get_title()
            content = self._editor_view.get_content()
            self._on_editor_save_requested(title, content)

    def _on_editor_save_requested(self, title: str, content: str) -> None:
        """Salva a nota ativa com o texto e título passados pelo editor (ou Ctrl+S)."""
        if not self.controller.current_note:
            if self._lbl_status:
                self._lbl_status.set_label("Nenhuma nota aberta para salvar.")
            return

        success = self.controller.save_current_note(title=title, content=content)
        if success:
            note = self.controller.current_note
            if self._tree_view and note:
                self._tree_view.update_tags_for_file(note.path, note.tags)
            if self._lbl_status and note:
                timestamp = note.updated_at.strftime('%H:%M:%S') if note.updated_at else ''
                tags_info = f" • {len(note.tags)} tags" if note.tags else ""
                self._lbl_status.set_label(f"💾 Nota salva: {Path(note.path).name} às {timestamp}{tags_info}")

    def _on_editor_content_changed(self, title: str, content: str) -> None:
        """Notificado quando o usuário digita no editor."""
        pass

    def _on_new_note_clicked(self, _widget: object) -> None:
        """Cria uma nova nota na raiz do workspace e atualiza a árvore."""
        note = self.controller.create_new_note()
        if note:
            self._on_refresh_workspace(None)
            self._on_file_selected(note.path)

    def _on_delete_file_requested(self, file_path: str) -> None:
        """Exclui a nota selecionada com confirmação do usuário."""
        file_name = Path(file_path).name
        confirmed = show_confirm_dialog(
            self,
            "Excluir Nota",
            f"Deseja realmente excluir permanentemente a nota '{file_name}'?",
        )
        if confirmed:
            was_active = (
                self.controller.current_note is not None
                and Path(self.controller.current_note.path).resolve() == Path(file_path).resolve()
            )
            deleted = self.controller.delete_note(file_path)
            if deleted:
                if was_active and self._editor_view:
                    self._editor_view.clear()

                self._on_refresh_workspace(None)
                if self._lbl_status:
                    self._lbl_status.set_label(f"Nota excluída: {file_name}")

    def _on_rename_file_requested(self, file_path: str) -> None:
        """Solicita novo nome e renomeia o arquivo Markdown."""
        current_name = Path(file_path).name
        current_stem = Path(file_path).stem
        new_name = show_prompt_dialog(
            self,
            "Renomear Nota",
            f"Novo nome para '{current_name}':",
            default_text=current_stem,
        )
        if new_name:
            try:
                renamed_note = self.controller.rename_note(file_path, new_name)
                if renamed_note:
                    self._on_refresh_workspace(None)
                    self._on_file_selected(renamed_note.path)
                    if self._lbl_status:
                        self._lbl_status.set_label(f"Nota renomeada para: {Path(renamed_note.path).name}")
            except Exception as e:
                logger.error(f"Erro ao renomear nota: {e}")
                if self._lbl_status:
                    self._lbl_status.set_label(f"Erro ao renomear nota: {e}")

    def _on_rename_folder_requested(self, folder_path: str) -> None:
        """Solicita novo nome e renomeia a pasta."""
        current_name = Path(folder_path).name
        new_name = show_prompt_dialog(
            self,
            "Renomear Pasta",
            f"Novo nome para a pasta '{current_name}':",
            default_text=current_name,
        )
        if new_name:
            try:
                new_folder = self.controller.rename_folder(folder_path, new_name)
                if new_folder:
                    self._on_refresh_workspace(None)
                    if self._lbl_status:
                        self._lbl_status.set_label(f"Pasta renomeada para: {new_folder.name}")
            except Exception as e:
                logger.error(f"Erro ao renomear pasta: {e}")
                if self._lbl_status:
                    self._lbl_status.set_label(f"Erro ao renomear pasta: {e}")

    def _on_create_file_in_folder_requested(self, folder_path: str) -> None:
        """Cria uma nova nota dentro da pasta especificada."""
        note = self.controller.create_new_note(folder_path=folder_path)
        if note:
            self._on_refresh_workspace(None)
            self._on_file_selected(note.path)

    def _on_create_folder_requested(self, parent_path: str) -> None:
        """Solicita nome e cria uma nova subpasta dentro do diretório pai."""
        parent_name = Path(parent_path).name
        folder_name = show_prompt_dialog(
            self,
            "Nova Subpasta",
            f"Criar nova subpasta dentro de '{parent_name}':",
            default_text="Nova Pasta",
        )
        if folder_name:
            created = self.controller.create_folder(parent_path, folder_name)
            if created:
                self._on_refresh_workspace(None)
                if self._lbl_status:
                    self._lbl_status.set_label(f"Pasta criada: {folder_name}")

    def _on_create_root_folder_clicked(self, _widget: object) -> None:
        """Cria uma pasta na raiz do workspace ativo."""
        active_vault = self.controller.get_active_vault()
        if not active_vault:
            if self._lbl_status:
                self._lbl_status.set_label("Abra um workspace antes de criar uma pasta.")
            return

        self._on_create_folder_requested(active_vault.path)

    def _on_delete_folder_requested(self, folder_path: str) -> None:
        """Exclui a pasta selecionada e todo o seu conteúdo com confirmação."""
        folder_name = Path(folder_path).name
        confirmed = show_confirm_dialog(
            self,
            "Excluir Pasta",
            f"Deseja realmente excluir a pasta '{folder_name}' e todo o seu conteúdo?",
        )
        if confirmed:
            # Limpa o editor se a nota ativa estava dentro da pasta
            if self.controller.current_note:
                note_resolved = Path(self.controller.current_note.path).resolve()
                if Path(folder_path).resolve() in note_resolved.parents:
                    if self._editor_view:
                        self._editor_view.clear()

            deleted = self.controller.delete_folder(folder_path)
            if deleted:
                self._on_refresh_workspace(None)
                if self._lbl_status:
                    self._lbl_status.set_label(f"Pasta excluída: {folder_name}")

    def _on_refresh_workspace(self, _widget: object) -> None:
        """Atualiza a lista de arquivos da árvore."""
        self.controller.refresh_workspace()
        active_vault = self.controller.get_active_vault()
        root_path = active_vault.path if active_vault else None
        tree_data = self.controller.get_workspace_tree()
        if self._tree_view:
            self._tree_view.populate(tree_data, root_path=root_path)
        if self._lbl_status:
            self._lbl_status.set_label("Workspace recarregado.")

    def _on_toggle_sidebar(self, _widget: object) -> None:
        """Mostra ou esconde a barra lateral."""
        if self._sidebar_box:
            is_visible = self._sidebar_box.get_visible()
            self._sidebar_box.set_visible(not is_visible)

    def _on_show_about(self, _widget: object) -> None:
        """Exibe o diálogo Sobre."""
        dialog = Gtk.AboutDialog(transient_for=self, modal=True)
        dialog.set_program_name("MarkAtlas")
        dialog.set_version(default_config.version)
        dialog.set_comments("Gestão de Conhecimento e PKM em Markdown (Offline-First)")
        dialog.set_authors(["Equipe MarkAtlas"])
        dialog.run()
        dialog.destroy()

    def _on_toggle_theme(self, _widget: object) -> None:
        """Manipula a alternância entre tema escuro e claro via menu."""
        new_theme = "light" if default_config.theme == "dark" else "dark"
        StyleManager.apply_theme(new_theme)
        if self._editor_view:
            self._editor_view.refresh_preview()
        logger.info(f"Tema alterado para: {new_theme}")

    def _open_url(self, url: str) -> None:
        """Abre uma URL no navegador padrão do sistema operacional."""
        try:
            webbrowser.open_new_tab(url)
            logger.info(f"Abrindo URL no navegador: {url}")
            if self._lbl_status:
                self._lbl_status.set_label(f"Abrindo documentação: {url}")
        except Exception as e:
            logger.error(f"Erro ao abrir URL {url}: {e}")

    # --- Acessibilidade: Atalhos e Manipuladores de Tamanho de Fonte ---

    def _on_main_key_press_event(self, widget: object, event: object) -> bool:
        """Captura atalhos globais de teclado da janela principal (Ctrl++, Ctrl+-, Ctrl+0)."""
        if not GTK_AVAILABLE or not hasattr(event, "state") or not hasattr(event, "keyval"):
            return False

        is_ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        if is_ctrl:
            # Aumentar Fonte (Ctrl + + / Ctrl + = / Ctrl + Numpad +)
            if event.keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
                self._on_increase_font()
                return True

            # Reduzir Fonte (Ctrl + - / Ctrl + _ / Ctrl + Numpad -)
            if event.keyval in (Gdk.KEY_minus, Gdk.KEY_underscore, Gdk.KEY_KP_Subtract):
                self._on_decrease_font()
                return True

            # Restaurar Fonte Padrão (Ctrl + 0 / Ctrl + Numpad 0)
            if event.keyval in (Gdk.KEY_0, Gdk.KEY_KP_0):
                self._on_reset_font()
                return True

        return False

    def _on_increase_font(self) -> None:
        """Aumenta o tamanho da fonte do editor e preview."""
        if self._editor_view:
            new_size = self._editor_view.increase_font_size()
            if self._lbl_status:
                self._lbl_status.set_label(f"🔍 Tamanho da fonte: {new_size}px")

    def _on_decrease_font(self) -> None:
        """Reduz o tamanho da fonte do editor e preview."""
        if self._editor_view:
            new_size = self._editor_view.decrease_font_size()
            if self._lbl_status:
                self._lbl_status.set_label(f"🔍 Tamanho da fonte: {new_size}px")

    def _on_reset_font(self) -> None:
        """Restaura o tamanho padrão da fonte do editor e preview."""
        if self._editor_view:
            new_size = self._editor_view.reset_font_size()
            if self._lbl_status:
                self._lbl_status.set_label(f"🔍 Tamanho da fonte restaurado: {new_size}px (padrão)")

