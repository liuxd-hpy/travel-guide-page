# 小红书取材手册（五条铁律 + 可复用代码）

## 铁律 0 · 登录态自检 + 让用户扫码（不要一上来就让人登录）

**不要在开场就要求用户登录。** 先接收需求，先做完全不依赖图源的事（核实票价、闭馆日、
预约窗口、算时间轴和预算），**在真正要抓图之前**再自检登录态。这样用户从发一句话到看到
《行程总览表》之间不需要被打断一次。

**未登录时小红书搜索页是空的**，且不会有任何报错：

| 现象 | 判据 |
|---|---|
| 搜索结果为空 | `search.feeds._value` 为空数组 |
| DOM 提示 | `document.body.innerText` 含「登录后查看搜索结果」 |
| API 直连失败 | `POST /api/sns/web/v1/search/notes` → **HTTP 500**（缺 `x-s` 签名） |

**别绕过登录**（抓 API / 改 header 都没用，签名是服务端下发的）。

### 自检登录态（抓图前跑一次）

```js
(() => {
  const t = document.body.innerText || '';
  // 1) cookie 有登录态特征
  const ck = document.cookie;
  const hasSession = /(web_session|a1|webId)/.test(ck);
  // 2) 导航栏已登录形态：出现「首页 / 消息 / 我」，且没有「登录」按钮
  const nav = [...document.querySelectorAll('.channel-bar a, .nav-bar a, header a')]
    .map(a => a.innerText.trim()).filter(Boolean);
  const logged = hasSession && nav.includes('首页') && !t.includes('登录后查看搜索结果');
  return JSON.stringify({ logged, hasSession, nav: nav.slice(0, 12), cookieLen: ck.length });
})()
```

`logged === true` → 直接开始抓，不要打扰用户。
`logged === false` → 走下面的登录引导。

### 未登录时的正确做法

1. `browser.tabs.open("https://www.xiaohongshu.com/explore")` → `focus: true`，把这个 tab 交给用户
2. **在同一个 tab 里注入一个提示遮罩**，写清「请扫码登录」+「登录完成后点击下方按钮」，并挂一个按钮
3. **等用户点按钮**，不要自己轮询导航栏去猜（用户可能正在输验证码、或手机还没拿出来）
4. 按钮点击后**再校验一次登录态**；`logged === true` 才继续
5. 登录态存在浏览器 profile 里，后续所有 tab 共享，**整个任务只需登录一次**

遮罩代码（直接注入，`SIDEBAR` 无关，纯 DOM）：

```js
(() => {
  if (document.getElementById('__xhs_login_gate')) return 'already';
  const d = document.createElement('div');
  d.id = '__xhs_login_gate';
  d.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:rgba(20,18,16,.82);' +
    'display:flex;align-items:center;justify-content:center;font:15px/1.7 system-ui,sans-serif';
  d.innerHTML =
    '<div style="background:#fffdf8;border-radius:18px;padding:34px 40px;max-width:520px;text-align:center;' +
    'box-shadow:0 24px 70px rgba(0,0,0,.5)">' +
    '<div style="font-size:34px;margin-bottom:10px">📱</div>' +
    '<h3 style="margin:0 0 12px;font-size:20px;color:#1a1d21">请先登录小红书</h3>' +
    '<p style="margin:0 0 8px;color:#5a6169">用手机 App 扫描下方二维码完成登录，<br>' +
    '登录态会保留在浏览器里，本次任务只需登录一次。</p>' +
    '<p style="margin:0 0 22px;color:#8a929a;font-size:13px">' +
    '为什么必须要登录：未登录时小红书的搜索结果是空的，而且不报错。</p>' +
    '<button id="__xhs_ok" style="font:inherit;font-weight:700;cursor:pointer;' +
    'background:#b13a24;color:#fff;border:0;border-radius:11px;padding:13px 30px">' +
    '✅ 我已登录，继续</button>' +
    '<p id="__xhs_hint" style="margin:16px 0 0;color:#b13a24;font-size:13px;min-height:20px"></p>' +
    '</div>';
  document.body.appendChild(d);
  document.getElementById('__xhs_ok').addEventListener('click', () => {
    const ck = document.cookie;
    const nav = [...document.querySelectorAll('.channel-bar a, .nav-bar a, header a')]
      .map(a => a.innerText.trim());
    const ok = /(web_session|a1|webId)/.test(ck) && nav.includes('首页');
    if (ok) { d.remove(); window.__XHS_LOGIN_OK = true; }
    else document.getElementById('__xhs_hint').textContent =
      '还没检测到登录态，请确认已在手机 App 里点确认，再点一次。';
  });
  return 'gate-injected';
})()
```

等待与确认：

```js
// 轮询用户是否点了「我已登录」；最多等 3 分钟
for (let i = 0; i < 36; i++) {
  const v = await tools.browser["evaluate"]({
    tabID: tabID, script: "window.__XHS_LOGIN_OK === true ? 'y' : 'n'" });
  if (v.value === 'y') break;
  await tools.browser["evaluate"]({ tabID: tabID, script: "new Promise(r=>setTimeout(r,5000))" });
}
```

确认成功后再 `browser.tabs.close` 掉这个登录 tab，后续关键词开新 tab 抓取。

### 什么时候提前自检

- 用户说「图片来源：不要小红书 / 我自己提供图」→ **全程不用问登录**
- 交付形态只要一份很短的行程（无实拍需求）→ 可跳过抓图，但仍建议问一句
- 已在本次会话早前登录过 → 复用，不要重复弹遮罩

---

## 铁律 1 · 搜索只认 `__INITIAL_STATE__`，但**必须抢在它被删之前**

`__INITIAL_STATE__` 是 SSR 注入的**一次性**数据源：Vue 应用 boot 后会把它整个 `delete`。
**慢一步就永久拿不到。**

```js
// ✅ 提取（字段是 camelCase，别写 snake_case）
(() => {
  const st = window.__INITIAL_STATE__;
  const f = st?.search?.feeds?._value || [];
  return f.filter(x => x?.id && x?.noteCard).map(x => {
    const nc = x.noteCard, ii = nc.interactInfo || {}, c = nc.cover || {};
    return {
      id: x.id, tk: x.xsecToken || '',
      t: (nc.displayTitle || '').replace(/\s+/g,' ').slice(0, 40),
      l: +ii.likedCount || 0, c: +ii.collectedCount || 0, s: +ii.sharedCount || 0,
      w: c.width || 0, h: c.height || 0, u: c.urlDefault || ''
    };
  });
})()
```

### 三个必踩的坑

**坑 1 · SPA 路由不会重新注入 `__INITIAL_STATE__`**
在同一个 tab 里 `navigate` 到另一个搜索 URL，前端可能只做 history 路由跳转、不做整页加载 →
`__INITIAL_STATE__` 既没有新数据、旧的也已删除，结果恒为 0。

> **解法：每个关键词开一个新 tab，采完即关。**

```js
for (const kw of KEYWORDS) {
  const t = await tools.browser["tabs.open"]({
    url: "https://www.xiaohongshu.com/search_result?keyword=" + encodeURIComponent(kw) + "&type=51",
    focus: false
  });
  await tools.browser["wait"]({ tabID: t.id, condition: "text", text: "赞", timeoutMs: 15000 }).catch(()=>{});
  // 立刻读，不要再 wait("load")
  const v = await tools.browser["evaluate"]({ tabID: t.id, script: EXTRACT });
  ...
  await tools.browser["tabs.close"]({ tabID: t.id });
}
```

**坑 2 · store 键位会变，`search.feeds` 不一定存在**
不同版本把数组放在 `search.feeds._value` / `search.feeds._rawValue` / `search.searchFeedsWrapper`。
拿不到时用**盲搜**兜底（找任意「含 `noteCard` 的对象数组」）：

```js
(() => {
  const found = []; const seen = new Set();
  (function walk(o, path, depth) {
    if (!o || typeof o !== 'object' || depth > 5 || found.length > 3) return;
    if (seen.has(o)) return; seen.add(o);
    if (Array.isArray(o)) {
      if (o.length && o[0] && o[0].noteCard) { found.push({ path, len: o.length }); return; }
      o.slice(0,2).forEach((x,i) => walk(x, path + '[' + i + ']', depth + 1));
      return;
    }
    for (const k of Object.keys(o).slice(0,40)) walk(o[k], path + '.' + k, depth + 1);
  })(window.__INITIAL_STATE__?.search, 'search', 0);
  return found;
})()
```

**坑 3 · 抓 DOM 的裸链接没有 token**
`a[href*="/explore/"]` 拿到的是 `/explore/<id>`，无 token → 点击必 404。token 只在 `__INITIAL_STATE__` 里。
（`/explore` 首页推荐流的 DOM href 反而**带** token，别被误导成「DOM 里没有 token」——那是首页的特例。）

---

## 铁律 2 · 链接必须带 `xsec_token`

```
https://www.xiaohongshu.com/explore/<24位id>?xsec_token=<token>&xsec_source=pc_search
```

- token 需 URL 编码（结尾常带 `=` → `%3D`）。`build.py` 用 `urllib.parse.quote(tk, safe="")` 处理
- ❌ `/discovery/item/<id>` 老格式 404；❌ 裸 `/explore/<id>` 404「你访问的页面不见了」
- ✅ 交付前**实测 2–3 条**：标题含笔记名、正文无「页面不见了/无法浏览/404」
- **token 会过期**，每行索引表必须再加兜底：
  `https://www.xiaohongshu.com/search_result?keyword=<标题>&type=51`

---

## 铁律 3 · HD 原图只认 `noteDetailMap[].note.imageList`

**唯一能拿到「一篇笔记内部全部图片」且带 HD 变体的入口。**
打开笔记详情页后**立刻**读（同样会被删）：

```js
// https://www.xiaohongshu.com/explore/<id>?xsec_token=<tk>&xsec_source=pc_search 之后
(() => {
  const map = window.__INITIAL_STATE__?.note?.noteDetailMap;
  if (!map) return [];
  const k = Object.keys(map).find(x => map[x]?.note?.imageList?.length);
  if (!k) return [];
  const note = map[k].note;
  return {
    title: (note.title || '').slice(0, 30),
    imgs: note.imageList
      .filter(x => /!nd_dft_w/.test(x.urlDefault || '') && x.width >= 1000)
      .slice(0, 6)
      .map(x => ({ u: (x.urlDefault || '').replace(/^http:/, 'https:'), w: x.width, h: x.height }))
  };
})()
```

| 变体 | 实测尺寸 | 来源 |
|---|---|---|
| `!nc_n_webp_prv_1` | 640px（压得很狠，~8KB） | DOM 里的 `img.src` —— **别用** |
| `!nc_n_webp_mw_1` | 仍 640px | 搜索接口 `cover.urlDefault` —— **不够清晰** |
| **`!nd_dft_wlteh_webp_3`** | **1080px** | `noteDetailMap.imageList`（竖图） |
| **`!nd_dft_wgth_webp_3`** | 1440–1920px | 同上（横图） |

**不要试图改后缀**（`wlteh→wltehj`、`hd_1`、去后缀）——CDN 路径 hash 与变体绑定，改了必 403。

### DOM 挑图是**降级方案**，不是主方案

```js
(() => {
  const imgs = Array.from(document.images).filter(x => /xhscdn/.test(x.src) && x.naturalWidth > 900);
  if (!imgs.length) return null;
  const b = imgs.sort((a, c) => c.naturalWidth - a.naturalWidth)[0];
  return { src: b.src, w: b.naturalWidth, h: b.naturalHeight };
})()
```

局限：**详情页只预载封面**，其余图是懒加载的小图 → `imgs.length` 常常只有 1。
所以它只能用来校验封面，**拿不到内部图**。

---

## 铁律 4 · 封面几乎不能直接用（本次实测命中率 29%）

小红书笔记封面**系统性偏设计稿**。实测一批 17 张封面，只有 5 张能直接进正文：

| 封面类型 | 处理 |
|---|---|
| 多格拼图（2×2 / 九宫格 / 备忘录截图） | ❌ 删 |
| 大字文案卡（大标题压在实拍上） | ❌ 删 |
| 标注箭头 + 说明框（「顶楼7楼 kaws娃娃 ↑」） | ❌ 删 |
| 密集信息图 / 攻略长图 | ❌ 删 |
| 展柜官方小标签（竖排「辛追夫人木椁 汉1F」） | ✅ **留**（实物标签，不是后期文案） |
| 纯实拍风景 / 人像 / 食物 | ✅ 留 |

> **正确流程：关键词搜索 → 取头部笔记 → 逐篇拉 `imageList` 全量入池 → 下载整池 → contact sheet 人工筛。**
> 一篇头部笔记给 4–6 张候选，6–8 篇就够撑起一章。单篇只取封面会毁掉整章。

---

## 铁律 5 · 多批次下载会**互相覆盖文件名**

`xhs_dl.py` 按 `i` 命名 `img/hNN.webp`，并把自己的结果写进 `have.json`。
如果你为扩充候选跑了第 2、3 批（`pool2.json` / `pool3.json`），**后一批会把前一批的 `h01.webp`… 直接盖掉**，
而 `have.json` 只记录最后一批 → 文件与数据不一致，build 时静默拿到错误的图。

> **正确流程：**
> 1. 分批采集，把每批结果**汇总写进同一个 `cands.json`**（key 重新连续编号）
> 2. 只跑 **一次** `xhs_dl.py cands.json`
> 3. 中途要重下，必须先 `Remove-Item -Recurse -Force img,sheet`

---

## 排序

`score = 赞 + 3×收藏 + 5×分享`（收藏/分享是更强的执行意图信号），每关键词取前 5–6 **篇笔记**（不是 5–6 张图）。

## 下载

```python
headers = {"User-Agent": "<Chrome UA>", "Referer": "https://www.xiaohongshu.com/",
           "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}
```

- 必须带 Referer，否则 403
- **CDN 链接带时间签名，当天抓当天用**，隔天全部 403
- 拿到原图后按 `quality=66~68, method=5~6` 重编码 webp 再内嵌（40 张 1080 图约 11MB → 6MB）
- **不要缩放**（缩到长边 1080 会变成 810×1080，等于降级）

## 选图标准（contact sheet 人工过一遍）

**留**：纯实拍风景/人像/食物、构图干净、光线好、主体明确
**删**：多格拼图九宫格、大字文案卡、纯文字封面、截图（含界面元素）、同质化重复场景、明显糊/暗/构图歪

**贴图技巧**：换图预览要用**全新文件名**（同名覆盖会读到旧缓存图）。
一屏 6 列 × 3 行最好读；批次多时看 `sheet_1.png`、`sheet_2.png`… 逐张过。

## 一次性把抓取结果落盘

code mode 里**不能写文件**（也不能 `import fs`）。做法：
1. `execute` 里跑搜索循环，返回**已筛选的候选数组**（含 id/token/互动数/**全量 HD URL**）
2. 立刻用 `write` 工具把数组写成 `cands.json`（**不要**在会话里攒着，数据会被截断丢失）
3. `python xhs_dl.py cands.json --proxy=""` 下载 + 拼 contact sheet
4. 看图挑选后，把入选的 key 写进页面模板

## 参考产出格式 `cands.json`

```json
[
 {"i":1,"g":"橘子洲","t":"笔记标题","l":4242,"c":4376,"s":4539,
  "id":"69467af2...","tk":"ABVx...=",
  "u":"https://sns-webpic-qc.xhscdn.com/...!nd_dft_wlteh_webp_3"}
]
```

> `g` 会被 contact sheet 当标签显示，**短一点**（如 `橘洲2`、`省博`、`IFS顶`），方便一屏扫完。