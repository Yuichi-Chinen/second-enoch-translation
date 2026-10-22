"""第二エノク書 日本語訳 読書版（A5・縦書き）のHTMLを生成する。

使い方:
    python build.py                 # 目次のページ番号なしでHTMLを出力
    python build.py --pages p.json  # p.json（章ID→ページ番号）を目次に反映して出力

PDF化は make_pdf.ps1 が行う（Edgeで印刷 → ページ番号取得 → 再印刷）。
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "第二エノク書"
OUT = HERE / "第二エノク書_読書版.html"

# (ID, ファイル名の接頭辞, 扉の小見出し, 扉の題, 章の範囲, 章見出しの接頭辞, 章IDの接頭辞)
PARTS = [
    ("pmain", "第", "本文", "エノクの秘密の書", "第一章〜第六十八章", "第", "c"),
    ("pappx", "付録第", "付録", "メルキゼデクの書", "付録第一章〜第五章", "付録第", "a"),
]

KANJI = "〇一二三四五六七八九"


def kanji_num(n: int) -> str:
    """1〜999 を「十」「百」を用いた漢数字にする。"""
    if n == 0:
        return "〇"
    out = ""
    h, t, o = n // 100, n // 10 % 10, n % 10
    if h:
        out += ("" if h == 1 else KANJI[h]) + "百"
    if t:
        out += ("" if t == 1 else KANJI[t]) + "十"
    if o:
        out += KANJI[o]
    return out


def tate(text: str) -> str:
    """縦組み用に数字・括弧・ダッシュを整える（HTMLエスケープ済みの文字列を返す）。"""
    text = text.replace("(", "（").replace(")", "）")
    # 数字の範囲を示すダッシュ（14–15）は「〜」に
    text = re.sub(r"(?<=\d)\s*[–\-]\s*(?=\d)", "〜", text)

    def num(m):
        s = m.group(0)
        if "." in s:
            a, b = s.split(".", 1)
            return "".join(KANJI[int(c)] for c in a) + "・" + "".join(KANJI[int(c)] for c in b)
        if len(s) >= 4 or s.startswith("0"):
            return "".join(KANJI[int(c)] for c in s)
        return kanji_num(int(s))

    text = re.sub(r"\d+(?:\.\d+)?", num, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def parse_chapter(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    num = int(re.search(r"第(\d+)章", lines[0]).group(1))
    subtitle = ""
    for ln in lines[1:6]:
        m = re.fullmatch(r"\*(.+)\*", ln.strip())
        if m:
            subtitle = m.group(1)
            break
    verses, notes = [], []  # verses: (label, text, 異文か)
    label, variant, in_ja, started = None, False, False, False
    for ln in lines:
        if ln.startswith("### "):
            head = ln[4:].strip()
            m = re.match(r"(\d+)(?:〜(\d+))?節", head)
            label = None if not m else (
                kanji_num(int(m.group(1))) + ("〜" + kanji_num(int(m.group(2))) if m.group(2) else ""))
            variant = "異文" in head
            in_ja, started = False, True
        elif ln.strip() == "**日本語訳**":
            in_ja = True
        elif ln.startswith("> **訳注**"):
            notes.append(re.sub(r"^> \*\*訳注\*\*[:：]\s*", "", ln))
        elif in_ja and ln.startswith(">"):
            verses.append((label, ln.lstrip("> ").strip(), variant))
        elif not started and ln.startswith(">"):
            # 最初の節より前の段落（第1章冒頭の、写本Aのみに見える序文）
            verses.append(("序", ln.lstrip("> ").strip(), False))
        elif in_ja and ln.strip() and not ln.startswith(">"):
            in_ja = False
    return num, subtitle, verses, notes


def build(pages: dict) -> str:
    def pg(key):
        return str(pages[key]) if key in pages else ""

    toc, body = [], []
    for pid, prefix, part_no, part_name, span, ch_prefix, id_prefix in PARTS:
        toc.append(f'<li class="toc-part"><a href="#{pid}"><span class="t">{part_no}　{part_name}</span>'
                   f'<span class="leader"></span><span class="n">{pg(pid)}</span></a></li>')
        body.append(f'<section class="part-title" id="{pid}"><div class="pt-inner">'
                    f'<p class="pt-no">{part_no}</p><h1>{part_name}</h1><p class="pt-span">{span}</p>'
                    f'</div></section>')
        files = sorted(SRC.glob(f"{prefix}[0-9][0-9]章.md"), key=lambda p: int(re.search(r"\d+", p.stem).group()))
        body.append('<section class="part">')
        for f in files:
            num, subtitle, verses, notes = parse_chapter(f)
            cid = f"{id_prefix}{num}"
            title = f"{ch_prefix}{kanji_num(num)}章"
            toc.append(f'<li class="toc-ch"><a href="#{cid}"><span class="t">{title}'
                       f'{"　<small>" + tate(subtitle) + "</small>" if subtitle else ""}</span>'
                       f'<span class="leader"></span><span class="n">{pg(cid)}</span></a></li>')
            out = [f'<article class="chapter"><h2 id="{cid}">{title}</h2>']
            if subtitle:
                out.append(f'<p class="subtitle">{tate(subtitle)}</p>')
            for label, text, variant in verses:
                if label == "序":
                    out.append(f'<p class="preface">{tate(text)}</p>')
                    continue
                mark = f'<span class="v">{label}{"・異文" if variant else ""}</span>' if label else ""
                out.append(f"<p>{mark}{tate(text)}</p>")
            if notes:
                out.append('<aside class="notes"><p class="notes-h">訳注</p>')
                out.extend(f"<p>{tate(n)}</p>" for n in notes)
                out.append("</aside>")
            out.append("</article>")
            body.append("\n".join(out))
        body.append("</section>")

    template = (HERE / "template.html").read_text(encoding="utf-8")
    return template.replace("{{TOC}}", "\n".join(toc)).replace("{{BODY}}", "\n".join(body))


if __name__ == "__main__":
    pages = {}
    if "--pages" in sys.argv:
        pages = json.loads(Path(sys.argv[sys.argv.index("--pages") + 1]).read_text(encoding="utf-8"))
    OUT.write_text(build(pages), encoding="utf-8")
    print(OUT)
