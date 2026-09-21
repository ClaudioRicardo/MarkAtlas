"""Testes unitários completos para o serviço de parsing e renderização de Markdown (MarkdownService)."""

import unittest
from src.services.markdown_service import MarkdownService


class TestMarkdownService(unittest.TestCase):
    """Suíte de testes para conversão de Markdown para Pango Markup com sintaxe básica e estendida."""

    def setUp(self):
        self.service = MarkdownService()

    def test_atx_headings_rendering(self):
        """Valida que cabeçalhos ATX H1 a H6 são renderizados com tamanhos e pesos corretos."""
        md = "# Título 1\n## Título 2 {#custom-id}\n### Título 3"
        pango = self.service.render_to_pango(md)
        self.assertIn("size='xx-large'", pango)
        self.assertIn("size='x-large'", pango)
        self.assertIn("size='large'", pango)
        self.assertIn("Título 1", pango)
        self.assertIn("Título 2", pango)

    def test_setext_headings(self):
        """Valida que títulos Setext (com === e ---) são convertidos para H1 e H2."""
        md = "Título Setext 1\n===\n\nSubtítulo Setext 2\n---"
        pango = self.service.render_to_pango(md)
        self.assertIn("size='xx-large'", pango)
        self.assertIn("Título Setext 1", pango)
        self.assertIn("size='x-large'", pango)
        self.assertIn("Subtítulo Setext 2", pango)

    def test_inline_formatting_basic_and_extended(self):
        """Valida negrito, itálico, negrito+itálico, tachado, highlight, subscrito e sobrescrito."""
        md = "Texto com ***negrito e itálico***, **negrito**, *itálico*, ~~tachado~~, ==destaque==, H~2~O e X^2^."
        pango = self.service.render_to_pango(md)
        self.assertIn("<b><i>negrito e itálico</i></b>", pango)
        self.assertIn("<b>negrito</b>", pango)
        self.assertIn("<i>itálico</i>", pango)
        self.assertIn("<s>tachado</s>", pango)
        self.assertIn("destaque", pango)
        self.assertIn("rise='-4000'", pango)
        self.assertIn("rise='5000'", pango)

    def test_fenced_code_blocks(self):
        """Valida renderização de blocos de código com caixa, cabeçalho e realce de sintaxe."""
        md = "```python\ndef hello():\n    return 'world'\n```"
        pango = self.service.render_to_pango(md)
        self.assertIn("PYTHON", pango)
        self.assertIn("🐍", pango)
        self.assertIn("def", pango)
        self.assertIn("hello", pango)
        self.assertIn("monospace", pango)

    def test_tables_rendering(self):
        """Valida renderização tabular formatada de tabelas Markdown."""
        md = "| Sintaxe | Descrição |\n| --- | --- |\n| Cabeçalho | Título |\n| Parágrafo | Texto |"
        pango = self.service.render_to_pango(md)
        self.assertIn("<b>Sintaxe</b>", pango)
        self.assertIn("<b>Descrição</b>", pango)
        self.assertIn("Cabeçalho", pango)
        self.assertIn("Parágrafo", pango)
        self.assertIn("│", pango)

    def test_lists_and_checkboxes(self):
        """Valida listas não-ordenadas, ordenadas e checklists."""
        md = "- Item 1\n* Item 2\n+ Item 3\n- [ ] Tarefa pendente\n- [x] Tarefa concluída\n1. Primeiro passo"
        pango = self.service.render_to_pango(md)
        self.assertIn("•", pango)
        self.assertIn("☐", pango)
        self.assertIn("☑", pango)
        self.assertIn("1.", pango)

    def test_blockquotes_and_nested(self):
        """Valida renderização de citações simples e aninhadas."""
        md = "> Citação simples.\n>> Citação aninhada."
        pango = self.service.render_to_pango(md)
        self.assertIn("Citação simples.", pango)
        self.assertIn("Citação aninhada.", pango)
        self.assertIn("italic", pango)

    def test_images_and_links(self):
        """Valida imagens, links comuns, wikilinks e autolinks."""
        md = "Veja ![Logo](https://site.com/logo.png) e [Site](https://site.com) além de [[MinhaNota]] e <https://exemplo.org>."
        pango = self.service.render_to_pango(md)
        self.assertIn("🖼️", pango)
        self.assertIn("[Imagem: Logo]", pango)
        self.assertIn("Site", pango)
        self.assertIn("[[MinhaNota]]", pango)
        self.assertIn("https://exemplo.org", pango)

    def test_links_with_trailing_punctuation_and_hex_colors(self):
        """Valida que links como [The Markdown Guide](https://www.markdownguide.org)! não colidem com tags #hex."""
        md = "Confira [The Markdown Guide](https://www.markdownguide.org)! E também #tag e [Link](https://site.com#sec) aqui."
        pango = self.service.render_to_pango(md)
        self.assertIn("The Markdown Guide", pango)
        self.assertIn("#tag", pango)
        # Garante que não há tags quebradas como ?#38bdf8'?
        self.assertNotIn("?#", pango)
        self.assertNotIn("<span foreground='<span", pango)

    def test_footnotes(self):
        """Valida referências e definições de notas de rodapé com apóstrofos e formatação."""
        md = "Here's a sentence with a footnote. [^1]\n\n[^1]: This is the footnote."
        pango = self.service.render_to_pango(md)
        self.assertIn("[1]", pango)
        self.assertIn("[^1]:", pango)
        self.assertIn("This is the footnote.", pango)
        self.assertIn("Here's", pango)
        self.assertNotIn("&#x27;", pango)
        self.assertNotIn("?#", pango)

    def test_emoji_and_kbd(self):
        """Valida substituição de emojis e tag <kbd>."""
        md = "Pressione <kbd>Ctrl</kbd> + <kbd>S</kbd> para salvar :rocket: :tada:"
        pango = self.service.render_to_pango(md)
        self.assertIn("[ Ctrl ]", pango)
        self.assertIn("[ S ]", pango)
        self.assertIn("🚀", pango)
        self.assertIn("🎉", pango)

    def test_tags_highlighting_and_extraction(self):
        """Valida reconhecimento, destaque e extração de tags #tag."""
        md = "Nota sobre #produtividade e #MarkAtlas/sdd com detalhes."
        pango = self.service.render_to_pango(md)
        self.assertIn("#produtividade", pango)
        self.assertIn("#MarkAtlas/sdd", pango)

        tags = self.service.extract_tags(md)
        self.assertEqual(tags, ["produtividade", "markatlas/sdd"])

    def test_html_escaping(self):
        """Valida que caracteres especiais de XML/HTML são escapados com segurança."""
        md = "Código com <script>alert('xss')</script> e a & b > c"
        pango = self.service.render_to_pango(md)
        self.assertNotIn("<script>", pango)
        self.assertIn("&lt;script&gt;", pango)
        self.assertIn("&amp;", pango)
        self.assertIn("&gt;", pango)


    def test_complex_nested_formatting(self):
        """Valida que formatações aninhadas complexas (links em negrito, tabelas com links, etc.) geram XML Pango válido."""
        md = "# Cabeçalho com [Link](https://site.com) e **negrito**\n\nTexto com **[Link em Negrito](https://exemplo.org)** e *[Link em Itálico](https://exemplo.org)*.\n\n| Coluna | Link |\n| --- | --- |\n| Item 1 | [Ver Mais](https://site.com) |"
        pango = self.service.render_to_pango(md)
        self.assertIn("<b>", pango)
        self.assertIn("</b>", pango)
        self.assertIn("Link em Negrito", pango)
        self.assertIn("Link em Itálico", pango)
        self.assertIn("Ver Mais", pango)


if __name__ == "__main__":
    unittest.main()
