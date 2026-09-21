"""Tokens de cores para renderização de Markdown em Pango Markup."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    """Paleta de cores para renderização de Markdown, derivada do tema ativo.

    Centraliza todas as cores de preview que antes estavam hardcoded
    em render_to_pango() e _update_preview().
    """

    tag_color: str
    code_bg: str
    code_fg: str
    quote_color: str
    link_color: str
    h_color: str
    hl_bg: str
    hl_fg: str
    table_border: str
    table_header_bg: str
    sep_color: str
    bullet_color: str
    num_color: str
    bar_color: str

    @classmethod
    def for_theme(cls, is_dark: bool = True) -> "ThemeColors":
        """Factory que retorna a paleta de cores para o tema especificado.

        :param is_dark: True para tema escuro, False para tema claro
        :return: Instância imutável de ThemeColors
        """
        if is_dark:
            return cls(
                tag_color="#38bdf8",
                code_bg="#1e293b",
                code_fg="#f1f5f9",
                quote_color="#94a3b8",
                link_color="#60a5fa",
                h_color="#f8fafc",
                hl_bg="#ca8a04",
                hl_fg="#ffffff",
                table_border="#475569",
                table_header_bg="#1e293b",
                sep_color="#334155",
                bullet_color="#3b82f6",
                num_color="#38bdf8",
                bar_color="#3b82f6",
            )
        else:
            return cls(
                tag_color="#0284c7",
                code_bg="#e2e8f0",
                code_fg="#0f172a",
                quote_color="#475569",
                link_color="#2563eb",
                h_color="#0f172a",
                hl_bg="#fde047",
                hl_fg="#1f2937",
                table_border="#94a3b8",
                table_header_bg="#e2e8f0",
                sep_color="#cbd5e1",
                bullet_color="#2563eb",
                num_color="#0284c7",
                bar_color="#3b82f6",
            )
