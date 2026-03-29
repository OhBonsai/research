# Harness Engineering 十二要素 - 图片提示词

> 风格统一说明：古典欧洲手绘科研手稿配图风格（达芬奇/自然哲学时代），主体黑白石墨线稿，精细交叉排线阴影。仅在关键信息处以温暖蜡笔风格涂抹色彩（琥珀金、赭红、暖棕），形成视觉焦点。网格纸/羊皮纸底纹，细虚线标注箭头，手写体标签。**每张图上方以手绘书法字体标注类别标题。**

---

## C1 上下文生命周期管理（Context Lifecycle Management）

**视觉隐喻**：炼金术蒸馏装置 — 信息在四个玻璃容器中依次净化

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, Leonardo da Vinci natural philosophy era. At the top of the image, the main title "上下文生命周期管理" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Context Lifecycle Management" in refined handwritten Latin script (font size approximately 24pt). An alchemist's distillation apparatus with four interconnected glass vessels arranged left to right, labeled "Inject", "Monitor", "Compress", "Archive". Raw chaotic text fragments pour into the first vessel. Each subsequent vessel contains progressively cleaner, more crystallized content. A graduated measuring cylinder beside the apparatus shows a fill line at 40% marked with a warning symbol, glowing with soft amber crayon coloring. Above the 40% line, the glass cracks and fractures. Thin dashed annotation arrows connect components. Below the apparatus, a small spiral labeled "Death Spiral" shows a vortex of tangled text fragments consuming itself. Predominantly black and white graphite linework with fine crosshatching. Selective warm crayon-style color: amber/gold on the 40% threshold line and the purified crystal output in the final vessel. Clean, professional layout.
```

---

## C2 分层记忆架构（Layered Memory Architecture）

**视觉隐喻**：地质剖面图 — 三层记忆如沉积岩层，文件系统的树根贯穿其中

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, geological cross-section diagram. At the top of the image, the main title "分层记忆架构" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Layered Memory Architecture" in refined handwritten Latin script (font size approximately 24pt). Three distinct sedimentary rock layers exposed in a cliff face, each labeled with elegant handwritten text: top layer "Procedural Memory" (thin, crystalline, containing tiny etched rule tablets), middle layer "Episodic Memory" (amber-tinted fossils of past events and sessions embedded), bottom layer "Semantic Memory" (dense, filled with branching knowledge structures like mineral veins). A great tree grows from the surface, its root system penetrating all three layers — roots labeled "File System". At the cliff top, a small stone monument reads "AGENTS.md" serving as the entry point. Beside the cliff, a magnifying glass examines a single file with annotation "Everything is a File". Predominantly black and white graphite with fine crosshatching for rock textures. Selective warm crayon-style color: soft amber/gold highlighting the fossil layer (Episodic) and warm terracotta on the root system. Dashed annotation lines with handwritten labels throughout.
```

---

## C3 架构约束硬执行（Architectural Constraint Enforcement）

**视觉隐喻**：中世纪城堡防御蓝图 — 分层城墙与门禁系统

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, medieval fortress architectural blueprint. At the top of the image, the main title "架构约束硬执行" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Architectural Constraint Enforcement" in refined handwritten Latin script (font size approximately 24pt). A concentric castle viewed from above in cross-section, with five defensive rings labeled L0 through L4 from innermost to outermost. The innermost ring (L0 "Types") is a sealed vault with no gates leading inward. Each subsequent ring has controlled gates — arrows show allowed passage direction (outward only, high layers may access low layers, never reverse). Some gates have locks labeled "Contract", others have type-checking guards with shields labeled "Pydantic". At the fortress perimeter, a rejected intruder (a tangled prompt arrow) bounces off the wall with annotation "Prompt persuasion rejected — code enforcement only". A small callout box shows "6.7% → 68.3%" with a format change icon. Predominantly black and white graphite linework with architectural precision. Selective warm crayon-style color: soft amber/gold on the innermost vault (L0) and warm terracotta on the locked contract gates. Clean blueprint aesthetic with thin dashed measurement lines.
```

---

## C4 验证管道与自愈（Validation Pipeline & Self-Healing）

**视觉隐喻**：钟表匠的四站质检线 — 精密检验台依次排列，配有反馈回路

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, a watchmaker's precision inspection workshop. At the top of the image, the main title "验证管道与自愈" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Validation Pipeline & Self-Healing" in refined handwritten Latin script (font size approximately 24pt). Four sequential workstations arranged left to right on a long wooden bench, each with a different magnifying instrument: Station 1 "Build" (a simple lens checking if gears fit), Station 2 "Lint-Arch" (a protractor verifying angles and alignment), Station 3 "Test" (a spring tension tester), Station 4 "Verify" (a complete pocket watch being wound and tested end-to-end by a tiny mechanical hand). Between stations, conveyor arrows move the workpiece forward. A curved feedback arrow loops from Station 4 back to Station 1 labeled "Self-Healing Loop" with annotation "max 3 retries". At the end of the bench, a three-tier escalation ladder: "Self-correct → Retry → Human → Stop". A small placard reads "P ≠ NP: Verification is easier than generation". Predominantly black and white graphite with fine crosshatching on wood textures. Selective warm crayon-style color: soft amber/gold on the final verified watch and warm terracotta on the escalation ladder. Dashed annotation arrows throughout.
```

---

## C5 多Agent编排与隔离（Multi-Agent Orchestration & Isolation）

**视觉隐喻**：文艺复兴建筑工坊 — 总建筑师在高台指挥，工匠在各自隔间工作

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, Renaissance architecture workshop scene. At the top of the image, the main title "多Agent编排与隔离" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Multi-Agent Orchestration & Isolation" in refined handwritten Latin script (font size approximately 24pt). A master architect stands on an elevated platform at center, holding only a planning scroll and compass — annotation: "Coordinator: plans, delegates, summarizes — never touches stone". Below, four separate enclosed workstations (glass-walled chambers) each contain a craftsman working independently: one carving (labeled "Haiku — simple tasks"), one sculpting complex ornaments (labeled "Opus — deep reasoning"), one searching through blueprint scrolls (labeled "Flash — retrieval"), one reviewing another's work with a different-colored lens (labeled "Cross-model Review"). Clean walls between chambers prevent dust and debris from crossing — annotation: "Context Isolation". Each chamber has a small output slot where only a finished, wrapped result passes to the coordinator. Predominantly black and white graphite linework with architectural detail. Selective warm crayon-style color: soft amber/gold on the coordinator's planning scroll and warm terracotta on the isolation chamber walls. Thin dashed arrows show delegation flow.
```

---

## C6 自演化与熵治理（Self-Evolution & Entropy Governance）

**视觉隐喻**：植物园修剪图 — 一棵不断生长的大树，园丁修剪枯枝，落叶堆肥滋养新根

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, botanical illustration of a grand tree in a walled garden. At the top of the image, the main title "自演化与熵治理" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Self-Evolution & Entropy Governance" in refined handwritten Latin script (font size approximately 24pt). The tree represents the evolving Harness system. Three types of growth are annotated: "Passive (hot-path)" as small new shoots appearing naturally, "Active (explicit)" as carefully grafted branches with tags labeled "[user-confirmed]", "Background (GC)" as a gardener with pruning shears trimming four types of dead wood: "Contradictions", "Outdated", "Gaps", "Drift". Cut branches fall into a compost bin at the base labeled "Trace → Critic → Refiner". From the compost, rich soil feeds back into the roots — annotation: "Data Flywheel: deployment = training". A ratchet mechanism on the trunk prevents the tree from shrinking — annotation: "Ratchet Effect: compiled patterns become permanent infrastructure". A small calendar on the garden wall shows "6 months" with five tally marks — "Manus: 5 rewrites". Predominantly black and white graphite with fine botanical crosshatching. Selective warm crayon-style color: soft amber/gold on the healthy new growth and warm terracotta on the compost cycle. Elegant dashed annotation lines.
```

---

## C7 可拆卸性与模块化（Detachability & Modularity）

**视觉隐喻**：达芬奇式机械分解图 — 三层可拆卸的精密仪器，各层齿轮独立可替换

```
Hand-drawn pencil sketch on faint grid paper, classical European scientific manuscript style, Leonardo da Vinci mechanical exploded-view drawing. At the top of the image, the main title "可拆卸性与模块化" is written in large elegant Renaissance hand-drawn calligraphy in Chinese (font size approximately 48pt), all characters highlighted with soft amber crayon coloring, slightly tilted as if penned by a natural philosopher. Below it, a smaller subtitle "Detachability & Modularity" in refined handwritten Latin script (font size approximately 24pt). A complex precision instrument shown in three separated horizontal layers floating apart with dashed assembly lines between them. Top layer: "Application Layer" — a decorative clock face with hands and dials (business logic, no coupling). Middle layer: "Harness Core" — the main gear train, springs, and escapement mechanism (context management, validation, tool registry — model-agnostic). Bottom layer: "Model Adapter" — interchangeable engine modules, three different engine variants shown side by side (labeled "Claude", "GPT", "Gemini"), each fitting the same mounting interface. Annotation arrows show: "swap bottom layer only when changing models". A timeline arrow at the bottom shows three eras: "Prompt Eng. (2022-24) → Context Eng. (2025) → Harness Eng. (2026)". A callout box: "Same model Opus: #33 vs #5 with different Harness". Predominantly black and white graphite with mechanical precision crosshatching. Selective warm crayon-style color: soft amber/gold on the universal mounting interface between layers and warm terracotta on the interchangeable engine modules.
```

---

## C8 人机协作模型（Human-Agent Collaboration Model）

**视觉隐喻**：从瓦特调速器到船舶舵手 — 238年控制论同构

```
