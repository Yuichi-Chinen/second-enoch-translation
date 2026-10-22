"""印刷済みPDFの目次リンクから、各部・各章の開始ページを取り出して JSON に書く。

使い方: python pages.py <in.pdf> <out.json>
"""
import json
import sys

import fitz  # PyMuPDF

doc = fitz.open(sys.argv[1])
pages = {}
for page in doc:
    for link in page.get_links():
        if link.get("nameddest"):
            pages[link["nameddest"]] = link["page"] + 1  # 0始まり → 印刷ページ番号

if len(pages) != 75:  # 本文・付録の扉 2 + 本文68章 + 付録5章
    sys.exit(f"目次リンク数が想定と異なります: {len(pages)}")
json.dump(pages, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(f"{len(pages)} entries, {doc.page_count} pages")
