# -*- coding: utf-8 -*-
"""
下载小红书 HD 原图 + 拼 contact sheet 供人工挑选。

用法：
    python xhs_dl.py cands.json --proxy http://127.0.0.1:7897
    python xhs_dl.py cands.json --proxy "" --sheet-cols 5   # 不走代理时用 --proxy ""

输入 cands.json（由 browser 抓取后落盘）：
    [{"i":1,"g":"大峡谷","t":"标题","l":4242,"c":4376,"s":4539,
      "id":"...","tk":"...","u":"https://sns-webpic-qc.xhscdn.com/...!nd_dft_wlteh_webp_3"}]

输出：
    img/hNN.webp     下载的原图（保持原始分辨率，不缩放）
    have.json        下载结果（含 ok/尺寸/体积），交给 build.py
    sheet/sheet_1.png ...  拼接预览图，用于人工挑图

注意：CDN 链接带时间签名，**当天抓当天用**，隔天会全部 403。
"""
import argparse
import concurrent.futures
import io
import json
import os
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFont

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
REFERER = "https://www.xiaohongshu.com/"


def build_opener(proxy):
    if proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener()


def fetch(url, proxy, timeout=40):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": REFERER,
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
    })
    with build_opener(proxy).open(req, timeout=timeout) as r:
        return r.read()


def download(item, imgdir, proxy):
    key = item["i"]
    name = "h%02d.webp" % key if isinstance(key, int) else "h%s.webp" % key
    path = os.path.join(imgdir, name)
    err = ""
    for use_proxy in ([proxy, ""] if proxy else [""]):
        try:
            data = fetch(item["u"], use_proxy or None)
            if len(data) < 5000:
                raise RuntimeError("suspiciously small (%d B)" % len(data))
            with open(path, "wb") as f:
                f.write(data)
            im = Image.open(io.BytesIO(data))
            im.load()
            return dict(item, file=name, ok=True, w=im.width, h=im.height,
                        kb=round(len(data) / 1024.0, 1), fmt=im.format)
        except Exception as e:  # noqa: BLE001
            err = str(e)[:70]
    return dict(item, ok=False, err=err)


def make_sheets(rows, sheetdir, cols, cell_w=330, cell_h=430):
    os.makedirs(sheetdir, exist_ok=True)
    for f in os.listdir(sheetdir):
        if f.endswith(".png"):
            os.remove(os.path.join(sheetdir, f))
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()
    pad, label_h, per = 8, 30, cols * 3
    out = []
    for n in range(0, len(rows), per):
        chunk = rows[n:n + per]
        rws = (len(chunk) + cols - 1) // cols
        sh = Image.new("RGB", (cols * (cell_w + pad) + pad,
                               rws * (cell_h + label_h + pad) + pad), (22, 22, 26))
        d = ImageDraw.Draw(sh)
        for k, it in enumerate(chunk):
            r, c = divmod(k, cols)
            x = pad + c * (cell_w + pad)
            y = pad + r * (cell_h + label_h + pad)
            try:
                im = Image.open(os.path.join(IMGDIR, it["file"]))
                im.load()
                im = im.convert("RGB")
                im.thumbnail((cell_w, cell_h))
                sh.paste(im, (x + (cell_w - im.width) // 2, y + (cell_h - im.height) // 2))
            except Exception as e:  # noqa: BLE001
                d.text((x + 10, y + 10), "ERR " + str(e)[:22], fill=(255, 120, 120), font=font)
            d.text((x + 3, y + cell_h + 4), "#%s %s" % (it["i"], it.get("g", "")),
                   fill=(240, 240, 245), font=font)
            d.text((x + 3, y + cell_h + 24),
                   "%s/%s/%s" % (it.get("l", "-"), it.get("c", "-"), it.get("s", "-")),
                   fill=(190, 190, 200), font=font)
        name = "sheet_%d.png" % (n // per + 1)
        sh.save(os.path.join(sheetdir, name))
        out.append(name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cands", help="cands.json 路径")
    ap.add_argument("--proxy", default="http://127.0.0.1:7897")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--sheet-cols", type=int, default=6)
    ap.add_argument("--min-width", type=int, default=1000, help="小于此宽度视为非原图")
    args = ap.parse_args()

    base = os.path.dirname(os.path.abspath(args.cands))
    global IMGDIR
    IMGDIR = os.path.join(base, "img")
    sheetdir = os.path.join(base, "sheet")
    os.makedirs(IMGDIR, exist_ok=True)

    items = json.load(open(args.cands, encoding="utf-8"))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(lambda it: download(it, IMGDIR, args.proxy), items):
            results.append(r)

    ok = [r for r in results if r.get("ok")]
    bad = [r for r in results if not r.get("ok")]
    lowres = [r for r in ok if min(r["w"], r["h"]) < args.min_width]

    print("downloaded %d / %d" % (len(ok), len(results)))
    for r in bad:
        print("  FAIL  #%s %s" % (r["i"], r.get("err")))
    for r in lowres:
        print("  WARN  #%s 只有 %sx%s，可能不是原图" % (r["i"], r["w"], r["h"]))
    if ok:
        tot = sum(r["kb"] for r in ok)
        print("payload %.2f MB (avg %.0f KB)" % (tot / 1024.0, tot / len(ok) / 1024.0))
        for r in sorted(ok, key=lambda x: x["i"]):
            print("  #%-3s %-8s %sx%s %7.1fKB  %s" % (
                r["i"], r.get("g", ""), r["w"], r["h"], r["kb"], (r.get("t") or "")[:24]))

    ok.sort(key=lambda x: x["i"])
    json.dump(ok, open(os.path.join(base, "have.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    sheets = make_sheets(ok, sheetdir, args.sheet_cols) if ok else []
    print("sheets:", ", ".join(sheets))
    print("have.json 已写入:", os.path.join(base, "have.json"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())