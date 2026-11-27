# -*- coding: utf-8 -*-
"""_caption.py —— 论文式图注（RV-16）。

规矩（照 RV-16 与 GB/T 7713.2—2022 §5.4.3、CY/T 171—2019 §7.2 排）：
    · 图号＋题名居中置**图下**，图上不放标题；字号小于正文、不加粗；
    · 整图注置图题**下方**、左对齐、首行缩进 2 字、排字宽度不超图宽；
    · 中英混排靠字体栈逐字选型：西文与数字 Times New Roman，中文宋体 SimSun；
    · 各条用分号、末条句号；断行不切西文数字串。
"""
from __future__ import annotations

import re

from matplotlib import font_manager

NOTE_PT = 8.8
TITLE_PT = 10.5
LINE_SPACING = 1.6

LATIN_TOKEN = re.compile(r"[+\-−]?[A-Za-z0-9][A-Za-z0-9\.\-_/+:]*")
NO_LINE_START = "）】》〉”’〕、。，；：！？%‰"


def _prop(size: float) -> font_manager.FontProperties:
    """字体栈：Times 出西文，SimSun 出中文，逐字回落。"""
    return font_manager.FontProperties(family=["Times New Roman", "SimSun"], size=size)


def _tokens(text: str) -> list[str]:
    """把文本切成原子片段：西文/数字串整体不拆，其余逐字。"""
    out, i = [], 0
    while i < len(text):
        m = LATIN_TOKEN.match(text, i)
        if m:
            tok, i = m.group(0), m.end()
            if i < len(text) and text[i] in "%‰℃":
                tok, i = tok + text[i], i + 1
            um = re.match(r" ?(?:pp|s|h|m|km|dpi|pt|px)(?![A-Za-z])", text[i:])
            if um and re.fullmatch(r"[+\-−]?[0-9][0-9.,]*", tok):
                tok, i = tok + um.group(0), i + um.end()
            out.append(tok)
        else:
            out.append(text[i])
            i += 1
    return out


def _make_probe(fig, fp):
    p = fig.text(0, 0.5, "", fontproperties=fp)
    try:
        ren = fig.canvas.get_renderer()
    except Exception:  # 没有 renderer 时先画一次
        fig.canvas.draw()
        ren = fig.canvas.get_renderer()

    def width_pt(s: str) -> float:
        p.set_text(s)
        return p.get_window_extent(renderer=ren).width * 72 / fig.dpi

    return p, width_pt


def _wrap(fig, text: str, avail_pt: float, fp) -> list[str]:
    probe, width = _make_probe(fig, fp)
    lines, cur = [], ""
    for tok in _tokens(text):
        if cur and width(cur + tok) > avail_pt:
            if cur[-1] in NO_LINE_START and len(cur) > 1:
                lines.append(cur[:-1])
                cur = cur[-1] + tok
            else:
                lines.append(cur)
                cur = tok
        else:
            cur += tok
    if cur:
        lines.append(cur)
    for i in range(1, len(lines)):
        while (lines[i] and lines[i][0] in NO_LINE_START
               and width(lines[i - 1] + lines[i][0]) <= avail_pt * 1.02):
            lines[i - 1] += lines[i][0]
            lines[i] = lines[i][1:]
    probe.remove()
    return lines


def add_caption(fig, no: int, title: str, notes: list[str],
                lb: float, rb: float, pad: float = 0.20, gap: float = 0.10) -> None:
    """在图下写图题与图注，并按注行数反推所需下边距。

    lb / rb：图注左、右边界（图坐标）；pad：图注距图底边（英寸）；
    gap：图注末行与图题之间的间距（英寸）。
    """
    body = "　　" + "；".join(n.strip().rstrip("。") for n in notes) + "。"
    fp_note = _prop(NOTE_PT)
    fp_title = _prop(TITLE_PT)

    avail_pt = fig.get_figwidth() * (rb - lb) * 72 * 0.99
    lines = _wrap(fig, body, avail_pt, fp_note)

    fig_h = fig.get_figheight()
    h_notes = len(lines) * NOTE_PT * LINE_SPACING / 72
    need = pad + h_notes + gap + TITLE_PT / 72 + 0.05
    sp = fig.subplotpars
    fig.subplots_adjust(bottom=max(need / fig_h, sp.bottom), left=sp.left,
                        right=sp.right, top=sp.top, wspace=sp.wspace, hspace=sp.hspace)

    for i, ln in enumerate(lines):
        y_pt = pad * 72 + (len(lines) - 1 - i) * NOTE_PT * LINE_SPACING
        fig.text(lb, y_pt / (fig_h * 72), ln, fontproperties=fp_note,
                 ha="left", va="bottom", color="#262626")

    # 图号与题名：图与号之间 0.14 em 细空，号与题名之间 0.72 em 字身
    cap = f"图\u200a{no}\u2002\u2002{title}"
    fig.text(0.5, (pad * 72 + h_notes * 72 + gap * 72) / (fig_h * 72), cap,
             fontproperties=fp_title, ha="center", va="bottom", color="#1a1a1a")
