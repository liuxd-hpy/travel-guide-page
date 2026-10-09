# -*- coding: utf-8 -*-
"""
给电脑版攻略页生成/刷新左侧二级目录（固定侧栏 + 滚动高亮 + 阅读进度条）。

用法：
    python scripts/sidebar.py page-desktop.html                 # 就地写回
    python scripts/sidebar.py page-desktop.html --out built.html # 写到别处
    python scripts/sidebar.py page-desktop.html --title "川藏线 24 天" --max-sub 12

工作方式（声明式，不做脆弱的字符串匹配）：
    1. 扫描 `<section id="sN">…</section>`，取每章 `.h2 h2` 的文字作为一级目录项。
    2. 扫描带 `data-toc` 属性的元素，按文档顺序作为该章的二级目录项：
         <h3 data-toc>机位 ① 来古冰川冰洞</h3>        → 自动取标题文字
         <div class="day" data-toc="D0–D5 康定 · 亚丁">  → 取属性值
       元素没有 id 时自动补一个（已带 id 的沿用原 id）。
    3. 注入 `<nav id="side">` + CSS + JS。重复运行会替换掉旧侧栏（幂等）。

设计约束：
    * **最多两级** —— data-toc 只挂在章节内的元素上，不会产生第三级。
    * 断点 ≥1280px 才显示；窄屏隐藏，回到模板自带的顶部目录盒。
    * 跳转用浏览器原生锚点（不劫持 click、不用 smooth 动画），
      因此禁用 JS 时链接依然可用，进度/高亮只是增强。
"""
import argparse
import io
import os
import re
import sys

CSS = """
/* ===== 左侧二级目录（由 scripts/sidebar.py 注入）===== */
/* SIDEBAR:CSS:BEGIN */
#side{position:fixed;left:0;top:0;width:252px;height:100vh;overflow-y:auto;overflow-x:hidden;
background:#14171a;color:#c8c2b6;padding:22px 0 44px;font-size:13.5px;line-height:1.5;z-index:60;border-right:1px solid #262b30}
#side::-webkit-scrollbar{width:6px}
#side::-webkit-scrollbar-thumb{background:#3a4149;border-radius:3px}
#side .side-hd{font-size:11.5px;letter-spacing:3px;color:#e9c98a;padding:0 20px 13px;
border-bottom:1px solid #262b30;margin-bottom:10px}
#side ol{list-style:none;margin:0;padding:0 12px}
#side a{display:block;text-decoration:none;color:#c8c2b6;padding:6px 10px;border-radius:8px}
#side a em{font-style:normal;color:#e9c98a;font-weight:800;margin-right:7px;font-size:12px}
#side a:hover{background:#1e2226;color:#fff}
#side ol ol{margin:0 0 4px 10px;padding:0 0 0 12px;border-left:1px solid #2c3238}
#side ol ol a{padding:4px 10px;font-size:12.6px;color:#8b939c}
#side ol ol a:hover{color:#e9c98a}
#side a.on{background:#b13a24;color:#fff}
#side a.on em{color:#fff}
#side ol ol a.on{background:transparent;color:#e9c98a;font-weight:700}
#side .side-bar{margin:16px 20px 0;height:3px;background:#262b30;border-radius:2px;position:sticky;bottom:8px}
#side .side-bar span{display:block;height:100%;width:0;background:#b9862f;border-radius:2px}
@media(min-width:1280px){body{padding-left:252px}}
@media(min-width:1280px){.toc{display:none}}
@media(max-width:1279px){#side{display:none}}
/* 跳转时给锚点目标留出顶部余量 */
section,.mapbox,.day-h,.day,h1,h2,h3,h4,.card,.tw,.tip,#gal{scroll-margin-top:18px}
/* SIDEBAR:CSS:END */
"""

JS = """
<script>
/* SIDEBAR:JS:BEGIN */
/* 左侧目录：滚动高亮 + 阅读进度（增强，非必需；无 JS 时锚点链接照常工作） */
(function(){
  var side=document.getElementById('side'); if(!side) return;
  var links=[].slice.call(side.querySelectorAll('a'));
  var tg=[];
  links.forEach(function(a){
    var el=document.getElementById(a.getAttribute('href').slice(1));
    if(el) tg.push({a:a, el:el, id:el.id});
  });
  var fill=document.getElementById('sidefill');
  var main=tg.filter(function(o){return /^s\\d+$/.test(o.id);});
  var sub=tg.filter(function(o){return !/^s\\d+$/.test(o.id);});
  function onScroll(){
    var h=document.documentElement.scrollHeight-window.innerHeight;
    if(fill) fill.style.width=(h>0?(window.pageYOffset/h*100):0)+'%';
    var cur=null;
    main.forEach(function(o){ if(o.el.getBoundingClientRect().top<=110) cur=o; });
    if(!cur) cur=main[0]||null;
    var cur2=null;
    if(cur){
      var top=cur.el.getBoundingClientRect().top;
      sub.forEach(function(o){ var q=o.el.getBoundingClientRect().top;
        if(q>=top-2 && q<=130) cur2=o; });
    }
    links.forEach(function(a){ a.classList.remove('on'); });
    if(cur) cur.a.classList.add('on');
    if(cur2) cur2.a.classList.add('on');
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  window.addEventListener('hashchange',onScroll);
  window.addEventListener('resize',onScroll);
  onScroll();
})();
/* SIDEBAR:JS:END */
</script>
"""

SEC_RE = re.compile(r'<section id="(s\d+)"')
TAG_RE = re.compile(r'<([a-zA-Z][\w-]*)((?:[^>"]|"[^"]*")*?)>')


def strip_tags(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = (s.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
          .replace('&nbsp;', ' ').replace('&quot;', '"'))
    return re.sub(r'\s+', ' ', s).strip()


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--out", default=None)
    ap.add_argument("--title", default=None, help="侧栏顶部标题，默认取 <title> 去掉「攻略」等后缀")
    ap.add_argument("--max-sub", type=int, default=12, help="单章二级项超过此数会告警")
    args = ap.parse_args()

    src = args.page
    html = io.open(src, encoding="utf-8").read()
    orig = html

    # ---- 0. 清掉旧侧栏，保证幂等 ----
    html = re.sub(r'<nav id="side"[\s\S]*?</nav>\s*', '', html)
    # 按显式哨兵注释整块删除。用哨兵而不是「猜下一个选择器」——
    # 猜测式删除会在注入块里含 @media / section 等选择器时提前截断，留下残渣逐次累积。
    html = re.sub(r'[ \t]*/\* SIDEBAR:JS:BEGIN \*/.*?/\* SIDEBAR:JS:END \*/\n?', '',
                  html, flags=re.S)
    html = re.sub(r'[ \t]*/\* SIDEBAR:CSS:BEGIN \*/.*?/\* SIDEBAR:CSS:END \*/\n?', '',
                  html, flags=re.S)
    # 兼容早期版本（无哨兵）的残留块
    html = re.sub(r'[ \t]*/\* ===== 左侧二级目录（由 scripts/sidebar\.py 注入）===== \*/[\s\S]*?'
                  r'(?=\n(?:\.|\}|h\d|section|footer|@media|\*|a\{|body|\.mapbox))', '', html)

    # ---- 1. 给 data-toc 元素补 id，并把标签文本带出来 ----
    subs = {}          # section_id -> [(anchor_id, label)]
    gen = [0]
    warnings = []

    def fix_tag(m):
        whole, tag, attrs = m.group(0), m.group(1), m.group(2)
        if 'data-toc' not in attrs:
            return whole
        val = None
        mv = re.search(r'data-toc\s*=\s*"([^"]*)"', attrs)
        if mv:
            val = mv.group(1).strip()
        mid = re.search(r'\bid\s*=\s*"([^"]*)"', attrs)
        if mid:
            aid = mid.group(1)
        else:
            gen[0] += 1
            aid = "toc-%d" % gen[0]
            attrs = re.sub(r'\sdata-toc', ' id="%s" data-toc' % aid, attrs, count=1)
        # 无值时取标签内文字
        if not val:
            tail = html[m.end():m.end() + 300]
            close = tail.find('</%s>' % tag)
            val = strip_tags(tail[:close] if close > 0 else tail)[:34]
        if not val:
            warnings.append('data-toc 元素 <%s> 未能取到标签文字' % tag)
            val = '未命名'
        # 归到最近的 section
        before = html[:m.start()]
        secs = SEC_RE.findall(before)
        sec = secs[-1] if secs else 's1'
        subs.setdefault(sec, []).append((aid, val))
        return '<%s%s>' % (tag, attrs)

    html = TAG_RE.sub(fix_tag, html)

    # ---- 2. 一级目录项 ----
    secs = []
    for m in SEC_RE.finditer(html):
        sec = m.group(1)
        chunk = html[m.end():m.end() + 1200]
        mh = re.search(r'<h2[^>]*>([\s\S]*?)</h2>', chunk)
        label = strip_tags(mh.group(1)) if mh else sec
        secs.append((sec, label))

    # ---- 3. 渲染导航 ----
    o = []
    o.append('<nav id="side" aria-label="目录">')
    o.append('  <div class="side-hd">%s</div>' % esc(args.title or '目录'))
    o.append('  <ol>')
    n1 = n2 = 0
    for sec, label in secs:
        o.append('    <li><a href="#%s"><em>%s</em>%s</a>'
                 % (sec, sec[1:].zfill(2), esc(label)))
        items = subs.get(sec, [])
        if items:
            if len(items) > args.max_sub:
                warnings.append('%s 有 %d 个二级项（>%d），建议合并'
                                % (sec, len(items), args.max_sub))
            o.append('      <ol>')
            for aid, txt in items:
                o.append('        <li><a href="#%s">%s</a></li>' % (aid, esc(txt)))
                n2 += 1
            o.append('      </ol>')
        o.append('    </li>')
        n1 += 1
    o.append('  </ol>')
    o.append('  <div class="side-bar"><span id="sidefill"></span></div>')
    o.append('</nav>')
    nav = "\n".join(o)

    # ---- 4. 注入（哨兵已被上面清干净，这里必然重建，实现真幂等）----
    if '</style>' not in html:
        print("ERROR: 找不到 </style>", file=sys.stderr)
        return 2
    html = html.replace('</style>', CSS + '</style>', 1)

    if '<body>' not in html:
        print("ERROR: 找不到 <body>", file=sys.stderr)
        return 2
    html = html.replace('<body>', '<body>\n\n' + nav, 1)

    if '</body>' not in html:
        print("ERROR: 找不到 </body>", file=sys.stderr)
        return 2
    html = html.replace('</body>', JS + '</body>', 1)

    out = args.out or src
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)

    print("章节（一级）：%d    二级项：%d" % (n1, n2))
    for sec, label in secs:
        items = subs.get(sec, [])
        print("  #%-4s %-22s 二级 %d" % (sec, label[:22], len(items)))
    print("levels: 2 (max)   injected: %d -> %d bytes" % (len(orig), len(html)))
    if warnings:
        print("WARN %d:" % len(warnings))
        for w in warnings:
            print("  " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())