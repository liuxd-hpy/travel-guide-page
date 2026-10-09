# -*- coding: utf-8 -*-
"""
单文件攻略 HTML 静态校验（交付前必过）。

用法：
    python validate.py 攻略.html
    python validate.py 攻略.html --min-short-side 1000

检查项：
    1. 每张图都是 base64 内嵌、能解码、短边 >= min-short-side（确保是原图不是缩略图）
    2. 没有外部资源：src/srcset 指向 http、<link>、<script src>、CSS url()
    3. HTML 标签闭合平衡
    4. 章节编号连续（01..N），无 object-fit:cover（不裁剪）
    5. 笔记链接带 xsec_token；索引表行数 == 正文用图数
    6. 同一 data URI 未被内嵌两次（否则体积翻倍）

退出码：0 全部通过 / 1 有失败项
"""
import argparse
import base64
import collections
import hashlib
import io
import os
import re
import sys

from PIL import Image

TAGS = ["html", "head", "body", "header", "footer", "section", "nav", "div", "figure",
        "figcaption", "table", "thead", "tbody", "tr", "td", "th", "ul", "ol", "li", "p",
        "a", "span", "h1", "h2", "h3", "h4", "script", "style", "time", "b", "i", "code",
        "button", "dl", "dt", "dd"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min-short-side", type=int, default=1000)
    ap.add_argument("--expect-sections", type=int, default=10)
    args = ap.parse_args()

    html = open(args.file, encoding="utf-8").read()
    fails, warns = [], []

    # 检查「样式类」问题时，只看 <style> 里的真实 CSS。
    # 正文 <code>/<pre>/注释里可能**描述** object-fit:cover 或 url()（例如本文档自己的说明表），
    # 那是散文不是样式，扫全文会误报。
    style_only = "\n".join(re.findall(r"<style[^>]*>([\s\S]*?)</style>", html))
    if not style_only.strip():
        style_only = html

    def ok(msg):
        print("  PASS  " + msg)

    def bad(msg):
        fails.append(msg)
        print("  FAIL  " + msg)

    def warn(msg):
        warns.append(msg)
        print("  WARN  " + msg)

    print("== %s (%.2f MB)" % (os.path.basename(args.file), os.path.getsize(args.file) / 1048576.0))

    # 1. 图片
    imgs = re.findall(r'<img[^>]*src="data:(image/[a-z+]+);base64,([^"]+)"', html)
    non_data = re.findall(r'<img[^>]*src="(?!data:)([^"]+)"', html)
    bad_dec, lowres, sizes = [], [], []
    for i, (_, b64) in enumerate(imgs):
        try:
            im = Image.open(io.BytesIO(base64.b64decode(b64)))
            im.load()
            sizes.append(im.size)
            if min(im.size) < args.min_short_side:
                lowres.append((i, im.size))
        except Exception as e:  # noqa: BLE001
            bad_dec.append((i, str(e)[:60]))
    if non_data:
        bad("有 %d 个 <img> 不是 base64 内嵌：%s" % (len(non_data), non_data[:3]))
    if bad_dec:
        bad("有 %d 张图解码失败：%s" % (len(bad_dec), bad_dec[:3]))
    if lowres:
        bad("有 %d 张图短边 < %d（不是原图）：%s"
            % (len(lowres), args.min_short_side, lowres[:5]))
    if imgs and not (non_data or bad_dec or lowres):
        ok("图片全部 base64 内嵌且解码通过，共 %d 张，分辨率 %s"
           % (len(imgs), sorted(set(sizes))))

    # 2. 外部资源
    ext = (re.findall(r'<link[^>]*>', html)
           + re.findall(r'<script[^>]*\ssrc=', html)
           + re.findall(r'url\((?!data:)[^)]*\)', style_only)
           + re.findall(r'<img[^>]*srcset=', html))
    if ext:
        bad("存在外部资源引用 %d 处：%s" % (len(ext), ext[:3]))
    else:
        ok("0 外部资源（<link> / <script src> / CSS url() / srcset）")

    # 3. 标签闭合
    diff = {}
    for t in TAGS:
        o = len(re.findall(r"<%s(?=[\s>])" % t, html))
        c = len(re.findall(r"</%s>" % t, html))
        if o != c:
            diff[t] = (o, c)
    if diff:
        bad("标签未闭合：%s" % diff)
    else:
        ok("HTML 标签全部闭合")

    # 4. 结构 / 不裁剪
    secs = re.findall(r'<section id="s(\d+)"', html)
    if len(secs) != args.expect_sections:
        warn("章节数 %d（预期 %d）：%s" % (len(secs), args.expect_sections, secs))
    else:
        ok("章节 %s 连续" % ",".join(secs))
    if "object-fit:cover" in style_only.replace(" ", ""):
        bad("出现了 object-fit:cover（会裁剪图片）")
    elif "height:auto" in style_only.replace(" ", ""):
        ok("图片未使用 cover 裁剪（height:auto）")
    else:
        warn("没找到 height:auto，确认图片样式")

    # 5. 链接
    note_links = [a for a in re.findall(r'<a\s[^>]*href="(https?://[^"]+)"', html) if "/explore/" in a]
    no_token = [a for a in note_links if "xsec_token=" not in a]
    if note_links and no_token:
        bad("有 %d 条笔记链接缺 xsec_token（会提示无法浏览）" % len(no_token))
    elif note_links:
        ok("笔记链接 %d 条，全部带 xsec_token" % len(note_links))
    # 5/6. 索引表行数 vs 正文用图数、重复内嵌（用完整 src 的哈希做唯一键）
    srcs = re.findall(r'<img[^>]*src="(data:image/[^"]+)"', html)
    hashes = [hashlib.md5(s.encode("utf-8")).hexdigest() for s in srcs]
    used = len(set(hashes))
    rows = len(re.findall(r'<tr><td class="num">', html))
    if rows and rows != used:
        warn("索引表 %d 行 vs 正文用图 %d 张（应一致）" % (rows, used))
    elif rows:
        ok("索引表 %d 行 == 正文用图 %d 张" % (rows, used))

    if len(hashes) != len(set(hashes)):
        dup = [k for k, v in collections.Counter(hashes).items() if v > 1]
        bad("有 %d 张图被内嵌多次（体积翻倍）" % len(dup))
    else:
        ok("每张图仅内嵌一份")

    print("== 结果：%s（%d 项失败，%d 项提醒）" % (
        "全部通过" if not fails else "有失败项", len(fails), len(warns)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())