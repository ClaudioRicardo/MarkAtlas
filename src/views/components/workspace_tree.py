"""Componente de Árvore de Arquivos e Sub-árvore de Tags do Workspace."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, Pango
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False
    Gtk = object  # type: ignore


class WorkspaceTreeView(Gtk.ScrolledWindow if GTK_AVAILABLE else object):  # type: ignore
    """Widget de árvore para navegação de diretórios, arquivos Markdown e menus contextuais."""

    COL_ICON = 0       # Ícone / Emoji (📁, 📄, 🏷️)
    COL_LABEL = 1      # Nome de exibição
    COL_TYPE = 2       # 'folder', 'file', 'tag'
    COL_PATH = 3       # Caminho absoluto ou nome da tag

    def __init__(
        self,
        on_file_selected: Optional[Callable[[str], None]] = None,
        on_tag_selected: Optional[Callable[[str, str], None]] = None,
        on_delete_file_requested: Optional[Callable[[str], None]] = None,
        on_create_file_in_folder_requested: Optional[Callable[[str], None]] = None,
        on_create_folder_requested: Optional[Callable[[str], None]] = None,
        on_delete_folder_requested: Optional[Callable[[str], None]] = None,
        on_rename_file_requested: Optional[Callable[[str], None]] = None,
        on_rename_folder_requested: Optional[Callable[[str], None]] = None,
    ) -> None:
        if not GTK_AVAILABLE:
            self.on_file_selected = on_file_selected
            self.on_tag_selected = on_tag_selected
            self.on_delete_file_requested = on_delete_file_requested
            self.on_create_file_in_folder_requested = on_create_file_in_folder_requested
            self.on_create_folder_requested = on_create_folder_requested
            self.on_delete_folder_requested = on_delete_folder_requested
            self.on_rename_file_requested = on_rename_file_requested
            self.on_rename_folder_requested = on_rename_folder_requested
            self.root_workspace_path: Optional[str] = None
            return

        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.get_style_context().add_class("workspace-tree-scrolled")

        self.on_file_selected = on_file_selected
        self.on_tag_selected = on_tag_selected
        self.on_delete_file_requested = on_delete_file_requested
        self.on_create_file_in_folder_requested = on_create_file_in_folder_requested
        self.on_create_folder_requested = on_create_folder_requested
        self.on_delete_folder_requested = on_delete_folder_requested
        self.on_rename_file_requested = on_rename_file_requested
        self.on_rename_folder_requested = on_rename_folder_requested
        self.root_workspace_path: Optional[str] = None

        # Model: [Icon: str, Label: str, Type: str, Path: str]
        self.store = Gtk.TreeStore(str, str, str, str)
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_headers_visible(False)
        self.tree_view.get_style_context().add_class("file-tree")

        self._setup_columns()
        self.tree_view.connect("cursor-changed", self._on_cursor_changed)
        self.tree_view.connect("row-activated", self._on_row_activated)
        self.tree_view.connect("button-press-event", self._on_button_press_event)

        self.add(self.tree_view)

    def _setup_columns(self) -> None:
        """Configura a coluna única com ícone e texto formatados."""
        column = Gtk.TreeViewColumn("Arquivos")
        column.set_spacing(6)

        # Renderer para Ícone
        renderer_icon = Gtk.CellRendererText()
        renderer_icon.set_property("scale", 1.05)
        column.pack_start(renderer_icon, False)
        column.add_attribute(renderer_icon, "text", self.COL_ICON)

        # Renderer para Nome do Arquivo/Tag
        renderer_text = Gtk.CellRendererText()
        renderer_text.set_property("scale", 1.05)
        renderer_text.set_property("ellipsize", Pango.EllipsizeMode.END)
        column.pack_start(renderer_text, True)
        column.add_attribute(renderer_text, "text", self.COL_LABEL)

        self.tree_view.append_column(column)

    def populate(self, tree_data: Dict[str, Any], root_path: Optional[str] = None) -> None:
        """Limpa e popula a árvore a partir do dicionário de estrutura do cofre."""
        if not GTK_AVAILABLE:
            return

        self.root_workspace_path = root_path or tree_data.get("path")
        self.store.clear()
        if not tree_data or "children" not in tree_data:
            return

        for child in tree_data["children"]:
            self._add_node(child, parent_iter=None)

    def _add_node(self, node: Dict[str, Any], parent_iter: Optional[object]) -> None:
        """Adiciona recursivamente nós de pastas e arquivos no TreeStore."""
        node_type = node.get("type", "file")
        name = node.get("name", "")
        path = node.get("path", "")

        if node_type == "folder":
            icon = "📁"
            current_iter = self.store.append(parent_iter, [icon, name, "folder", path])
            for child in node.get("children", []):
                self._add_node(child, current_iter)
        else:
            icon = "📄"
            self.store.append(parent_iter, [icon, name, "file", path])

    def update_tags_for_file(self, file_path: str, tags: List[str]) -> None:
        """
        Insere ou atualiza a sub-árvore de tags sob o nó do arquivo especificado.
        """
        if not GTK_AVAILABLE:
            return

        file_iter = self._find_iter_by_path(file_path)
        if not file_iter:
            return

        # Remove sub-nós anteriores de tags sob este arquivo
        child_iter = self.store.iter_children(file_iter)
        while child_iter:
            self.store.remove(child_iter)
            child_iter = self.store.iter_children(file_iter)

        # Insere as novas tags como nós filhos
        for tag in tags:
            tag_label = f"#{tag}"
            self.store.append(file_iter, ["🏷️", tag_label, "tag", tag])

        # Expande o nó do arquivo para exibir as tags
        tree_path = self.store.get_path(file_iter)
        self.tree_view.expand_row(tree_path, False)

    def _find_iter_by_path(self, target_path: str) -> Optional[object]:
        """Procura o TreeIter correspondente ao caminho do arquivo."""
        def search(iter_node: Optional[object]) -> Optional[object]:
            while iter_node:
                item_path = self.store.get_value(iter_node, self.COL_PATH)
                if item_path == target_path:
                    return iter_node

                if self.store.iter_has_child(iter_node):
                    child = self.store.iter_children(iter_node)
                    found = search(child)
                    if found:
                        return found

                iter_node = self.store.iter_next(iter_node)
            return None

        first_iter = self.store.get_iter_first()
        return search(first_iter)

    def _on_cursor_changed(self, treeview: object) -> None:
        """Disparado quando a seleção da linha muda."""
        selection = self.tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            return

        item_type = model.get_value(tree_iter, self.COL_TYPE)
        item_path = model.get_value(tree_iter, self.COL_PATH)

        if item_type == "file" and self.on_file_selected:
            self.on_file_selected(item_path)
        elif item_type == "tag" and self.on_tag_selected:
            parent_iter = model.iter_parent(tree_iter)
            parent_path = model.get_value(parent_iter, self.COL_PATH) if parent_iter else ""
            self.on_tag_selected(item_path, parent_path)

    def _on_row_activated(self, treeview: object, path: object, column: object) -> None:
        """Disparado ao dar duplo clique ou Enter em uma linha."""
        tree_iter = self.store.get_iter(path)
        if not tree_iter:
            return

        item_type = self.store.get_value(tree_iter, self.COL_TYPE)
        if item_type == "folder":
            if self.tree_view.row_expanded(path):
                self.tree_view.collapse_row(path)
            else:
                self.tree_view.expand_row(path, False)

    def _on_button_press_event(self, treeview: object, event: object) -> bool:
        """Disparado ao clicar na árvore (detecta clique com o botão direito)."""
        if event.button == 3:  # Botão direito
            path_info = self.tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info is not None:
                path, _col, _cell_x, _cell_y = path_info
                self.tree_view.get_selection().select_path(path)
                tree_iter = self.store.get_iter(path)
                if tree_iter:
                    item_type = self.store.get_value(tree_iter, self.COL_TYPE)
                    item_path = self.store.get_value(tree_iter, self.COL_PATH)
                    self._show_context_menu(event, item_type, item_path)
                    return True
            elif self.root_workspace_path:
                # Clique direito no espaço vazio abre opções do workspace raiz
                self._show_context_menu(event, "folder", self.root_workspace_path)
                return True
        return False

    def _show_context_menu(self, event: object, item_type: str, item_path: str) -> None:
        """Exibe o menu de contexto correspondente ao tipo de nó clicado."""
        menu = Gtk.Menu()

        if item_type == "file":
            mi_rename = Gtk.MenuItem(label="✏️ Renomear Nota...")
            if self.on_rename_file_requested:
                mi_rename.connect("activate", lambda _: self.on_rename_file_requested(item_path))
            menu.append(mi_rename)

            mi_delete = Gtk.MenuItem(label="🗑️ Excluir Nota...")
            if self.on_delete_file_requested:
                mi_delete.connect("activate", lambda _: self.on_delete_file_requested(item_path))
            menu.append(mi_delete)

        elif item_type == "folder":
            mi_new_note = Gtk.MenuItem(label="📄 Nova Nota nesta pasta...")
            if self.on_create_file_in_folder_requested:
                mi_new_note.connect("activate", lambda _: self.on_create_file_in_folder_requested(item_path))
            menu.append(mi_new_note)

            mi_new_folder = Gtk.MenuItem(label="📁 Nova Subpasta...")
            if self.on_create_folder_requested:
                mi_new_folder.connect("activate", lambda _: self.on_create_folder_requested(item_path))
            menu.append(mi_new_folder)

            # Verifica se não é a raiz do workspace
            is_root = False
            if self.root_workspace_path:
                is_root = Path(item_path).resolve() == Path(self.root_workspace_path).resolve()

            if not is_root:
                menu.append(Gtk.SeparatorMenuItem())
                mi_rename_folder = Gtk.MenuItem(label="✏️ Renomear Pasta...")
                if self.on_rename_folder_requested:
                    mi_rename_folder.connect("activate", lambda _: self.on_rename_folder_requested(item_path))
                menu.append(mi_rename_folder)

                mi_delete_folder = Gtk.MenuItem(label="🗑️ Excluir Pasta...")
                if self.on_delete_folder_requested:
                    mi_delete_folder.connect("activate", lambda _: self.on_delete_folder_requested(item_path))
                menu.append(mi_delete_folder)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)
