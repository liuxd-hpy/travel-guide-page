# -*- coding: utf-8 -*-
"""
把页面模板里的 token 替换成 base64 图片 / 笔记链接 / 互动数据索引表，产出单文件 HTML。

用法：
    python build.py page.html --data have.json --out 恩施攻略.html --quality 68

page.html 里可用的 token：
    @@IMG:<key>@@   图片位置，替换为 data:image/webp;base64,...
    @@U:<key>@@     笔记链接位置，替换为带 xsec_token 的可打开链接
    @@NOTES@@       索引表 <tbody> 内容，按正文首次出现顺序生成

规则：
    * 原图不缩放，只按 --quality 重编码 webp（1080 图 300KB -> 150KB，画感几乎无损）
    * 同一张图在正文只能出现一次；重复出现会让 base64 重复内嵌、体积翻倍（会告警）
    * 链接兜底：每行额外生成「搜同款」搜索链接，应付 token 过期
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.parse

from PIL import Image


def _norm(k):
    """把 key 归一化：1 / "1" / "01" 视为同一个（页面里常写两位数 01，cands 里是整数 1）。"""
    k = str(k).strip()
    return str(int(k)) if k.isdigit() else k


def encode(path, quality, method):
    im = Image.open(path)
    im.load()
    if im.mode != "RGB":
        im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, method=method)
    return buf.getvalue(), im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", help="已填好内容的页面模板 page.html")
    ap.add_argument("--data", default="have.json", help="xhs_dl.py 产出的 have.json")
    ap.add_argument("--out", required=True, help="输出的单文件 HTML")
    ap.add_argument("--quality", type=int, default=68)
    ap.add_argument("--method", type=int, default=5)
    ap.add_argument("--scale", type=int, default=0,
                    help=">0 时把长边缩到这个值（默认 0 = 保持原图不缩放）")
    args = ap.parse_args()

    tpl = open(args.page, encoding="utf-8").read()
    data_path = args.data if os.path.isabs(args.data) else os.path.join(
        os.path.dirname(os.path.abspath(args.page)), args.data)
    have = {_norm(r["i"]): r for r in json.load(open(data_path, encoding="utf-8"))}

    # 图片所在目录 = have.json 同级的 img/
    imgdir = os.path.join(os.path.dirname(os.path.abspath(data_path)), "img")

    keys = []
    for m in re.finditer(r"@@(?:IMG|U):([^@]+)@@", tpl):
        k = _norm(m.group(1))
        if k not in keys:
            keys.append(k)
    missing = [k for k in keys if k not in have]
    if missing:
        print("ERROR: have.json 里没有这些 key:", missing)
        return 2

    usage = {}
    for m in re.finditer(r"@@IMG:([^@]+)@@", tpl):
        k = _norm(m.group(1))
        usage[k] = usage.get(k, 0) + 1
    dup = {k: v for k, v in usage.items() if v > 1}
    if dup:
        print("WARN  这些图在正文出现多次，base64 会被重复内嵌（体积 ×%d）：" % max(dup.values()))
        for k, v in dup.items():
            print("       #%s 出现 %d 次" % (k, v))

    cache, payload = {}, 0
    for k in keys:
        r = have[k]
        raw, size = encode(os.path.join(imgdir, r["file"]), args.quality, args.method)
        if args.scale and max(size) > args.scale:
            im = Image.open(io.BytesIO(raw))
            im.thumbnail((args.scale, args.scale))
            b = io.BytesIO()
            im.save(b, format="WEBP", quality=args.quality, method=args.method)
            raw = b.getvalue()
        payload += len(raw)
        cache["IMG:" + k] = "data:image/webp;base64," + base64.b64encode(raw).decode("ascii")
        tk = urllib.parse.quote(r.get("tk", ""), safe="")
        cache["U:" + k] = ("https://www.xiaohongshu.com/explore/%s"
                           "?xsec_token=%s&xsec_source=pc_search" % (r.get("id", ""), tk))
        r["out_kb"] = round(len(raw) / 1024.0, 1)

    def _repl(m):
        kind = "IMG" if m.group(0).startswith("@@IMG") else "U"
        return cache.get("%s:%s" % (kind, _norm(m.group(1))), m.group(0))

    html = re.sub(r"@@(?:IMG|U):([^@]+)@@", _repl, tpl)

    # 索引表：只列正文真正用到的图
    rows, n = [], 0
    for k in keys:
        if "IMG:" + k not in cache or k not in usage:
            continue
        r = have[k]
        n += 1
        title = (r.get("t") or "实拍笔记").replace("<", "&lt;").replace(">", "&gt;")
        search = ("https://www.xiaohongshu.com/search_result?keyword="
                  + urllib.parse.quote((r.get("t") or "")[:18]) + "&type=51")
        rows.append(
            '<tr><td class="num">%d</td><td>%s<br><span style="color:#8a919b;font-size:12.5px">%s</span></td>'
            '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td>'
            '<td><a href="%s" target="_blank" rel="noopener">打开笔记 ↗</a><br>'
            '<a href="%s" target="_blank" rel="noopener" style="color:#8a919b">搜同款 ↗</a></td></tr>'
            % (n, title, r.get("g", ""), r.get("l", "-"), r.get("c", "-"), r.get("s", "-"),
               cache["U:" + k], search))
    html = html.replace("@@NOTES@@", "\n      ".join(rows))

    left = sorted(set(re.findall(r"@@[^@\s]{1,40}@@", html)))
    if left:
        print("ERROR: 还有未替换的 token:", left[:10])
        return 2

    out = args.out if os.path.isabs(args.out) else os.path.join(
        os.path.dirname(os.path.abspath(args.page)), args.out)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    for k in keys:
        r = have[k]
        if "out_kb" in r:
            print("  #%-3s %-8s %sx%s -> %6.1f KB" % (k, r.get("g", ""), r["w"], r["h"], r["out_kb"]))
    print("images: %d   payload: %.2f MB   file: %.2f MB"
          % (len(usage), payload / 1048576.0, os.path.getsize(out) / 1048576.0))
    print("out:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())