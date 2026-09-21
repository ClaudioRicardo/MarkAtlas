"""Testes unitários para o SyntaxHighlighter e caixas de código de programação."""

import unittest

from src.services.markdown.syntax_highlighter import SyntaxHighlighter
from src.services.markdown.theme_colors import ThemeColors
from src.services.markdown_service import MarkdownService


class TestSyntaxHighlighter(unittest.TestCase):
    """Suíte de testes para o motor de destaque de sintaxe e caixas de código."""

    def setUp(self):
        self.highlighter = SyntaxHighlighter()
        self.markdown_service = MarkdownService()
        self.dark_colors = ThemeColors.for_theme(is_dark=True)
        self.light_colors = ThemeColors.for_theme(is_dark=False)

    def test_python_code_block_rendering(self):
        """Valida que código Python recebe cabeçalho com ícone e destaque de sintaxe."""
        code = """def hello(name: str) -> bool:
    # Comentário explicativo
    print(f"Olá {name}")
    return True"""

        result = self.highlighter.render_code_block(code, "python", self.dark_colors)

        # Cabeçalho com ícone e nome da linguagem
        self.assertIn("🐍", result)
        self.assertIn("PYTHON", result)

        # Borda da caixa fechada (top, lateral, bottom)
        self.assertIn("┌──", result)
        self.assertIn("│", result)
        self.assertIn("└", result)

        # Numeração de linhas
        self.assertIn("1", result)
        self.assertIn("4", result)

        # Destaque de palavras-chave e tokens
        self.assertIn("def", result)
        self.assertIn("return", result)
        self.assertIn("True", result)
        self.assertIn("foreground=", result)

    def test_javascript_code_block_rendering(self):
        """Valida destaque de sintaxe para JavaScript."""
        code = """const calculate = (a, b) => {
    // Retorna a soma
    return a + b;
};"""
        result = self.highlighter.render_code_block(code, "javascript", self.dark_colors)
        self.assertIn("🟨", result)
        self.assertIn("JAVASCRIPT", result)
        self.assertIn("const", result)
        self.assertIn("return", result)

    def test_sql_code_block_rendering(self):
        """Valida destaque de sintaxe para SQL."""
        code = "SELECT id, name, email FROM users WHERE active = 1 ORDER BY created_at DESC;"
        result = self.highlighter.render_code_block(code, "sql", self.dark_colors)
        self.assertIn("🗄️", result)
        self.assertIn("SQL", result)
        self.assertIn("SELECT", result)
        self.assertIn("FROM", result)
        self.assertIn("WHERE", result)

    def test_json_code_block_rendering(self):
        """Valida destaque para blocos JSON."""
        code = '{\n  "name": "MarkAtlas",\n  "version": 1,\n  "offline": true\n}'
        result = self.highlighter.render_code_block(code, "json", self.dark_colors)
        self.assertIn("📄", result)
        self.assertIn("JSON", result)
        self.assertIn("MarkAtlas", result)

    def test_unspecified_language_renders_generic_box(self):
        """Valida que bloco sem linguagem especificada recebe cabeçalho genérico."""
        code = "plain text without syntax"
        result = self.highlighter.render_code_block(code, "", self.dark_colors)
        self.assertIn("CÓDIGO", result)
        self.assertIn("plain text without syntax", result)

    def test_xml_special_characters_escaping(self):
        """Valida que caracteres <, >, & são estritamente escapados para evitar corrupção de Pango Markup."""
        code = "if (x < 10 && y > 20) { return &ptr; }"
        result = self.highlighter.render_code_block(code, "c", self.dark_colors)
        self.assertIn("&lt;", result)
        self.assertIn("&gt;", result)
        self.assertIn("&amp;", result)

    def test_light_theme_uses_light_palette(self):
        """Valida que o tema claro utiliza cores escuras apropriadas para legibilidade."""
        code = "def authenticate():\n    return True"
        result_dark = self.highlighter.render_code_block(code, "python", self.dark_colors)
        result_light = self.highlighter.render_code_block(code, "python", self.light_colors)

        # Paleta escura usa #38bdf8 para keyword, paleta clara usa #0284c7
        self.assertIn("#38bdf8", result_dark)
        self.assertIn("#0284c7", result_light)

    def test_markdown_service_integration(self):
        """Valida integração ponta-a-ponta através do MarkdownService."""
        md = """Aqui está uma função:

```python
def add(a: int, b: int) -> int:
    return a + b
```
"""
        pango = self.markdown_service.render_to_pango(md, is_dark=True)
        self.assertIn("🐍", pango)
        self.assertIn("PYTHON", pango)
        self.assertIn("JetBrains Mono", pango)

    def test_mermaid_diagrams_are_not_confused_with_code_blocks(self):
        """Garante que blocos ```mermaid continuam sendo processados pelo motor de diagramas SVG."""
        md = """```mermaid
flowchart TD
    A --> B
```"""
        pango = self.markdown_service.render_to_pango(md, is_dark=True)
        self.assertIn("[ MERMAID DIAGRAM ]", pango)
        self.assertIn("🖼️ [Mermaid:", pango)

    def test_tsx_code_block_alignment(self):
        """Valida que código React/TSX com tags JSX (<Can />, <Button>) mantém a caixa fechada perfeitamente."""
        code = """export const Can: React.FC<CanProps> = ({ perform, children, fallback = null }) => {
    const { hasPermission } = usePermission();
    if (hasPermission(perform)) {
        return <>{children}</>;
    }
    return <>{fallback}</>;
};"""
        result = self.highlighter.render_code_block(code, "tsx", self.dark_colors)
        self.assertIn("⚛️", result)
        self.assertIn("REACT TSX", result)
        self.assertIn("┌──", result)
        self.assertIn("└", result)

        # Cada linha numerada deve começar e terminar com │
        lines = result.strip().split("\n")
        body_lines = [l for l in lines if "│" in l and "┌" not in l and "└" not in l]
        for bl in body_lines:
            self.assertTrue(bl.strip().startswith("<span foreground="), f"Linha não começa com borda: {bl}")
            self.assertTrue(bl.strip().endswith("│</span>"), f"Linha não termina com borda fechada: {bl}")


if __name__ == "__main__":
    unittest.main()
