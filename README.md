# travel-guide-page

把一段口述行程，变成一份**能双击打开、可离线转发**的单文件 HTML 图文攻略。

面向 AI 编码助手（[opencode](https://github.com/sst/opencode) / Claude Code 等）的 Skill：给它一句「做一份川藏线 24 天自驾攻略」，它会问你 8 个问题、抓 200 张小红书实拍原图、核实闭馆日和抢票时刻，最后产出两个 7 MB 的 HTML 文件——**零外链、零 CDN、断网也能看**。

> ### 👉 在线预览成品
> **[川藏线 24 天纯电自驾攻略（电脑版）](docs/guide-desktop.html)｜[手机版](docs/guide-mobile.html)**
> 2027/7/12 – 8/4 · 赣州→成都→珠峰→拉萨→昌都→成都 · 5563km · 最高 5248m · 4 人
> 36 张 1080px+ 实拍原图 · 10 章 · 左侧二级目录 · 3 张内联 SVG 地图 · 人均 14,646 元
>
> 就是这个 Skill 的真实产出，可以直接下载转发。

---

## 一、成品攻略里有什么

不是「一篇文章」，是一份**能真的照着开车的操作手册**。以下数字全部来自上面那份成品实测。

### 10 章骨架

| 章 | 内容 | 成品里的量 |
|---|---|---|
| **01 路线总览** | 全程地理位置图（经纬度投影）+ 逐段里程与充电点路线图 + 高速费用政策 | 2 张内联 SVG |
| **02 逐日行程** | 每天写死钟点：出发 / 换乘 / 充电 / 午餐 / 进园 / 到店 | **24 张日卡、170 个时间点** |
| **03 必去景点** | 4 个必去 + 2 个备选，各带门票、价格口径、换上去的时机 | 6 张卡片 |
| **04 打卡机位** | 4 个机位各配 3–5 张不同构图实拍 + 3 组拍照姿势 + 城市点位图 | 17 张图 + 1 张 SVG |
| **05 预约与开放** | 抢票日历（哪一天几点动手）+ 门票与开放时间表 + **抢不到票怎么办** | 1 张表 + 兜底方案 |
| **06 路况与证件** | 证件清单 + 六类高风险路段 + 停车与充电桩确认 | 3 组清单 |
| **07 纯电续航与充电** | **折算算式** + 逐日充电计划 + 超充绿廊 + 排队/衰减/托运 | 1 张表 + 12 次充电 |
| **08 一路吃什么** | 必点与顺路 + 按天数的饮食节奏 | 4 张图 |
| **09 预算分摊** | 逐项预算表（4 人分摊到人均）+ 省钱 6 招 | 1 张表 |
| **10 图库 & 笔记索引** | 正文全部实拍图汇总 + 22 篇原笔记链接与互动数据 | 36 图 + 22 条链接 |

合计：**24 张日卡 · 36 张图 · 36 张卡片 · 8 张表格 · 31 个提示框 · 3 张手绘地图 · 170 个时间点**

### 十个「别的攻略不会给你」的东西

1. **逐日时间轴写到钟点** —— 不是「第二天：然乌→林芝」，是「07:30 出发 → 08:15 波密检查站 → 09:40 然乌湖观景台停留 40min → 11:20 充电站充至 90%」。
2. **日期 × 闭馆日对撞** —— 布宫每周一闭馆且不售当日票、稻城亚丁旺季限流 15000/日。Skill 会算出「**哪一天几点必须动手抢票**」并顶在页面最前面。成品里是三个时点：现在办边防证 / 7-8 前约亚丁 7-15 门票 / 7-12 当天抢布宫 7-25 门票。
3. **纯电续航写算式不写标称** —— `真实续航 = CLTC × 电池健康度 × 高速折扣 × 高原系数`，成品算出 `470 × 0.9 × 0.7 × 0.92 = 272km/趟`，据此排 12 次途中充电，每个必充点写清「第几高速 · 第几公里 · 到站表显剩多少%」。
4. **返程不走回头路** —— 24 天要塞下「不走回头路」，唯一解是返程改走 G4218 拉萨→昌都→江达→德格→甘孜（约 2000km），而不是 318 折返。
5. **长途日主动拆分** —— 林芝→拉萨 435km/6.5h 拆成两天，因为中途必须充电，硬开会把疲劳驾驶拉到 7.5h+。
6. **预算精确到人均** —— 电费 946kWh×1.5、住宿 23 晚×2 间×260，最终 **4 人合计 58,584 元 / 人均 14,646 元**，Hero 区、正文小计、页脚摘要三处强制对齐。
7. **左侧二级目录** —— 10 个一级 + 31 个二级，滚动跟随高亮 + 阅读进度条。宽屏自动展开，窄屏回落到顶部目录盒。
8. **点图看大图，放大的是同一张原图** —— 不是另开一张压缩版。
9. **每张图能溯源** —— 配原笔记链接（带 `xsec_token`，能直接打开）+ 「搜同款」兜底 + 赞/藏/分享数据。
10. **离线双击可用** —— `src="http"` 为 0，图片全 base64 内嵌，地图是手绘 SVG，微信里转发、飞机上打开都不怕。

### 图片是怎么选的

不是抓下来就用。流程是：**搜 20 个关键词 → 391 篇笔记 → 按互动数据筛到 72 篇 → 拉全量图片入池 208 张 → contact sheet 人工过一遍 → 最终留 36 张**（保留率 50%）。

删除的典型：多格拼图、九宫格、大字文案卡、带界面元素的截图、标注箭头图、同质化重复场景。**小红书笔记封面实测可用率只有 29%**，所以候选池按最终用图数的 2–3 倍抓。

---

## 二、使用步骤

### Step 0 · 安装

```bash
git clone https://github.com/liuxd-hpy/travel-guide-page.git \
  ~/.config/opencode/skills/travel-guide-page
```

Windows：`%USERPROFILE%\.config\opencode\skills\travel-guide-page`
Claude Code 则是 `~/.claude/skills/travel-guide-page`。

> 目录名**必须**是 `travel-guide-page` —— 安装路径就是技能名。装完重启 opencode。

### Step 1 · 说一句话

```
做一份川藏线 24 天自驾攻略，7 月 12 号出发，纯电车 4 个人
```

### Step 2 · 回答 2–3 组问题

助手会**一次问完**关键参数，不会挤牙膏：

- **行程骨架**：出发地→目的地、出发日期+具体时间、返回日期+最晚到家时间、总天数
- **交通与预算**：自驾还是公共交通 → 自驾要车型 / 人数 / **纯电必须问「高速按几折算」** / 住宿档位 / 是否分摊预算
- **内容与交付**：必去景点、节奏（松/中/紧）、美食忌口、要不要「机位+姿势」章、交付形态（电脑版 / 手机版 / 两版）、**图片来源要不要小红书实拍**

> **纯电自驾一定要回答「高速按几折算」。** 这个数字决定充电次数，进而改写时间轴、路况提醒和电费预算。说不清就按 7 折算（国家电网+高速充电折扣常见区间），再乘电池健康度和高原衰减。
>
> 如果你说「图片来源不要小红书 / 我自己提供图」，**整个流程完全不需要登录**。

### Step 3 · 看《行程总览表》

助手会先核实票价、闭馆日、预约窗口，给你一屏总览表，**含「哪一天几点必须动手抢票」的醒目提示框**。确认或调整后才继续。

**到这一步为止，全程不需要登录小红书。**

### Step 4 · ⚠️ 需要扫码时，助手会主动弹窗

只有真正要抓图的那一刻，助手才**自检登录态**：

- **已登录** → 直接开抓，不打扰你
- **未登录** → 自动打开 `xiaohongshu.com/explore` 并弹出一个提示遮罩

遮罩长这样：

```
┌────────────────────────────────┐
│            📱                   │
│      请先登录小红书              │
│  用手机 App 扫描二维码完成登录    │
│                                │
│  为什么必须要登录：              │
│  未登录时搜索结果是空的，且不报错 │
│                                │
│   [ ✅ 我已登录，继续 ]          │
└────────────────────────────────┘
```

**你扫码 → 在手机上点确认 → 再点「我已登录，继续」。**

助手会等你点，不会自己去猜你登录好了没有。点完它再校验一次登录态，成功才继续。

> 登录态存在浏览器 profile 里，**整个任务只需登录一次**，后续所有标签页共享。
>
> 顺带提醒：约 70 次页面访问后会跳「安全验证」captcha，需要人工过一下。这是平台限流，不是 Skill 出错。

### Step 5 · 等它跑完

抓图和选图是耗时最长的环节（要人眼看 contact sheet 挑图）。跑完你会得到：

```
川藏线24天攻略-电脑版.html    7.57 MB
川藏线24天攻略-手机版.html    7.55 MB
```

### Step 6 · 转发

直接把 HTML 文件发微信 / 存网盘 / 邮件附件。对方双击就能看，**不需要联网、不需要装任何东西**。

---

## 三、它解决什么问题

| 需求 | 做法 |
|---|---|
| 不在流程开头打断你 | 登录自检放在**抓图前**，不是在开场。说一句话 → 答 3 组问题 → 看总览表，一路不被打断 |
| 需要扫码才停一次 | 自动打开小红书 + 弹提示遮罩，**等你点「我已登录」**才继续，不会自己猜 |
| 转发后对方能看 | 所有图片 base64 内嵌，CSS/JS 全内嵌，`src="http` 数量为 **0** |
| 断网 / 微信里能看 | 地图用**手绘内联 SVG**，不引任何地图服务 |
| 图片不被切掉脸 | 全站 `width:100%;height:auto`，禁止 `object-fit:cover` |
| 想看细节能放大 | 点任意图 → 全屏看**同一张原图**，ESC / 点空白 / 手机返回键关闭 |
| 图源可追溯 | 每张图配原始小红书笔记链接（带 `xsec_token`，**能直接打开**）+ 搜同款兜底 |
| 纯电不摸黑 | 续航折算写明算式，逐日充电计划写清「第几高速·第几公里·到站剩多少%」 |
| 长文档能跳转 | 电脑版自动生成左侧二级目录 + 滚动高亮 + 阅读进度条 |
| 关键数字别打架 | Hero 统计 / 预算合计 / 正文小计三处强制自洽 |

---

## 目录结构

```
travel-guide-page/
├── SKILL.md                      # 执行手册：Step 0–9 工作流
├── docs/                         # 成品示例（可直接在线浏览）
│   ├── index.html                # 演示页
│   ├── guide-desktop.html        # 电脑版成品
│   └── guide-mobile.html         # 手机版成品
├── references/
│   ├── intake.md                 # 交互问卷字段、纯电折扣换算、闭馆日对撞
│   ├── outline.md                # 01–10 章内容契约、CSS 类词汇、SVG 地图规范、侧栏规范
│   └── xhs-playbook.md           # 小红书抓取五条铁律 + 可复用代码
├── scripts/
│   ├── xhs_dl.py                 # 下载 HD 原图 + 拼 contact sheet
│   ├── build.py                  # 注入 base64 / 笔记链接 / 索引表
│   ├── sidebar.py                # 生成左侧二级目录（读 data-toc，幂等）
│   └── validate.py               # 静态四项校验
└── assets/
    ├── template-desktop.html     # 电脑版骨架（CSS/JS/图库/大图层已写好）
    └── template-mobile.html      # 手机版骨架
```

---

## 核心约束

### 五条铁律（违反即返工）

1. **单文件自包含** —— 图片 base64 内嵌，`src="http` 必须是 0
2. **图片不裁剪** —— `width:100%;height:auto`，全站禁止 `object-fit:cover`
3. **点图看大图** —— 放大的是同一张原图，不是另一张
4. **笔记链接能打开** —— 必须带 `xsec_token`，裸 `/explore/<id>` 会提示「无法浏览」
5. **原图 + 高互动** —— 只取 1080px 以上原图，只选赞/藏/分享都高的笔记，按 `赞 + 3×藏 + 5×分享` 排序

### 交付前五项校验

静态（`validate.py`）+ 浏览器 DOM 实测，全过才算完：

- 图片能 base64 解码且短边 ≥1000px
- 标签闭合平衡、章节编号连续、无 `cover` 裁切
- 笔记链接全带 token、无重复内嵌、索引表行数 == 用图数
- 逐张点开大图层，`#lbimg.src` 与原图 `src` **完全相同**
- 侧栏三级为 0、失效锚点为 0；SVG 文字越界数与重叠数均为 0

---

## 左侧二级目录（电脑版）

正文里想进目录的元素加个 `data-toc`，跑一次脚本，其余全自动：

```html
<div class="day" data-toc="D0–D5 康定 · 折多山 · 亚丁">   <!-- 文案取属性值 -->
<h4 class="mini" data-toc>抢票日历</h4>                   <!-- 文案自动取标题文字 -->
<div class="gal" id="gal" data-toc="实拍图库"></div>       <!-- 已有 id 的沿用 -->
```

```bash
python scripts/sidebar.py 攻略-电脑版.html --title "川藏线 24 天 · 目录"
```

自动补 id、注入 CSS/JS、**幂等**。最多两级：≥1280px 显示侧栏，窄屏回落到模板自带的顶部目录盒。跳转用浏览器原生锚点（不劫持 click、不用 smooth 动画），禁用 JS 时链接依然可用。

---

## 已知边界

- **必须先登录小红书**，否则搜索页是空的且不报错
- **小红书会限流**：约 70 次页面访问后跳安全验证 captcha，需人工过
- **CDN 图片链接带签名**，隔天会全 403 —— 所以必须当场下载转 base64，不能偷懒直接引外链
- **token 会失效**：`xsec_token` 有有效期，交付时必须给「搜同款」兜底链接（示例页里的链接可能已过期）
- **纯电续航折算是估算**：真实续航受风速、温度、载重、驾驶风格影响，正文会标注为参考值
- **票价/开放时间会变**：脚本抓的事实类数据都标「参考价」，出发前请用官方渠道复核

---

## 法律与合规

这个 Skill 会抓取小红书的用户上传图片，并在产出页面里内嵌。

- 生成的攻略**请自用或小范围分享**，不要作为商业产品再分发
- 页面已内置图片版权与 token 兜底说明，交付时不要删
- 自动化访问请控制频率，尊重平台 robots.txt 与用户协议
- 图片版权归原作者所有，来源链接已在第 10 章列出

`docs/` 下的示例成品仅用于**演示 Skill 能力**，其中 36 张照片版权归原作者所有，不在 MIT 授权范围内。

**用之前请确认你所在地和使用场景的合规要求。**

---

## License

MIT © 2026 travel-guide-page contributors

模板、脚本、文档可自由使用与修改。

---

<a name="english"></a>

## English summary

**travel-guide-page** is an AI-agent Skill that turns a spoken itinerary into a single, self-contained, offline-viewable HTML travel guide.

Feed it one sentence — *"build a 24-day self-drive guide for the Sichuan–Tibet route, departing July 12, 4 people, EV"* — and it will:

- Ask 2–3 batches of clarifying questions at once (dates, group size, vehicle type, **EV highway power discount**, lodging tier, dietary limits, deliverable form)
- Fact-check ticket prices, opening hours, **closed days**, and booking windows via web search, then compute *which day at what hour you must grab tickets*
- Scrape Xiaohongshu for real photos: search → rank by engagement → pull full HD image lists → download → hand-pick from contact sheets (cover images are usable only ~29% of the time)
- Emit a 10-chapter guide: route overview with inline SVG maps, hour-by-hour daily timeline, must-see spots with ticket strategy, photo positions & poses, booking calendar, road & document checklist, **EV range math with per-day charging plan**, food, per-person budget split, gallery + note index

**Output:** one `.html` file (typically 7–8 MB) with every image base64-embedded, zero external requests, no `object-fit: cover`, click-to-zoom lightbox, working Xiaohongshu source links, a scroll-spy two-level sidebar, and a hand-drawn SVG map — openable by double-click, even offline.

**Requirements:** Python 3.8+, and **a logged-in Xiaohongshu browser session** (search returns empty without it, silently).

Everything — scripts, templates, references — is MIT licensed. **Photographs in the `docs/` demo are not**: they belong to their original authors and are included for demonstration only.

[Back to top](#travel-guide-page)
