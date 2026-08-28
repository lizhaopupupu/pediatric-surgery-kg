# -*- coding: utf-8 -*-
"""知识图谱构建流程 + 35 部指南清单 组合图（kg_pipeline.png，v0.5）。
左侧：6 步构建流程；右侧：指南分"国内/国际"两列展示。
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))
from daimon_runtime import setup_plot

setup_plot()

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

mpl.rcParams.update({
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

C_DARK = "#1F4E79"
C_MID = "#2E75B6"
C_BG = "#EAF1F9"
C_ORANGE = "#C55A11"
C_GRAY = "#5A6E8C"

BASE = Path(__file__).resolve().parent
OUT = BASE / "knowledge_graph" / "kg_pipeline_v5.png"

kg = json.load(open(BASE / "knowledge_graph" / "kg5.json", encoding="utf-8"))

INTL_KEYS = ["ACR", "ESGE", "ESPGHAN", "ESPID", "NICE", "HerniaSurge", "NASPGHAN",
             "CUA", "AUA", "EAU", "WSES", "ACOG", "罗马"]
guides = [n for n in kg["nodes"] if n["id"].startswith("G")]
dom = [g for g in guides if not any(k in g["name"] for k in INTL_KEYS)]
intl = [g for g in guides if any(k in g["name"] for k in INTL_KEYS)]

steps = [
    ("指南检索与筛选", "PubMed / 中华系列期刊 / 学会官网\n纳入 35 部指南与专家共识"),
    ("Schema 定义", "9 类实体节点 + 11 类关系\n疾病·检查·影像征象·鉴别要点等"),
    ("实体与关系抽取", "逐条结构化整理指南要点\n鉴别诊断边带鉴别要点属性"),
    ("临床专家审核", "小儿外科医师核对实体、关系与要点\n剔除过时与低证据条目"),
    ("Neo4j 入库", "266 节点 / 401 关系 / 29 对鉴别边\n生成 Cypher 导入脚本"),
    ("多智能体调用", "检索增强推理\n为影像与文本智能体提供循证依据"),
]

fig = plt.figure(figsize=(11.6, 5.3))

# ---------------- 左：构建流程 ----------------
axL = fig.add_axes([0.015, 0.02, 0.33, 0.90])
axL.set_xlim(0, 1)
axL.set_ylim(0, 6.6)
axL.axis("off")
axL.text(0.5, 6.42, "知识图谱构建流程", ha="center", va="center",
         fontsize=13.5, fontweight="bold", color=C_DARK)

box_x, box_w, box_h, gap = 0.06, 0.88, 0.78, 0.22
top = 6.02
for i, (title, desc) in enumerate(steps):
    y = top - i * (box_h + gap) - box_h
    box = FancyBboxPatch((box_x, y), box_w, box_h,
                         boxstyle="round,pad=0.02,rounding_size=0.06",
                         facecolor=C_BG if i % 2 == 0 else "white",
                         edgecolor=C_MID, linewidth=1.4, zorder=2)
    axL.add_patch(box)
    axL.add_patch(plt.Circle((box_x + 0.075, y + box_h - 0.21), 0.075,
                             facecolor=C_DARK, edgecolor="none", zorder=3))
    axL.text(box_x + 0.075, y + box_h - 0.21, str(i + 1), ha="center", va="center",
             fontsize=10, color="white", fontweight="bold", zorder=4)
    axL.text(box_x + 0.18, y + box_h - 0.21, title, ha="left", va="center",
             fontsize=11.5, fontweight="bold", color=C_DARK, zorder=4)
    axL.text(box_x + 0.18, y + 0.26, desc, ha="left", va="center",
             fontsize=8.2, color="#444444", linespacing=1.35, zorder=4)
    if i < len(steps) - 1:
        axL.add_patch(FancyArrowPatch((box_x + box_w / 2, y - 0.005),
                                      (box_x + box_w / 2, y - gap + 0.005),
                                      arrowstyle="-|>", mutation_scale=16,
                                      color=C_MID, lw=1.8, zorder=1))

# ---------------- 右：指南清单（国内/国际两列） ----------------
axR = fig.add_axes([0.36, 0.02, 0.63, 0.90])
axR.set_xlim(0, 1)
axR.set_ylim(0, 21.2)
axR.axis("off")
axR.text(0.5, 20.85, "循证依据：35 部指南 / 专家共识", ha="center", va="center",
         fontsize=13.5, fontweight="bold", color=C_DARK)


def guide_col(x0, w, title, items, header_color):
    axR.add_patch(plt.Rectangle((x0, 19.6), w, 0.75, facecolor=header_color, edgecolor="none"))
    axR.text(x0 + 0.012, 19.6 + 0.375, title, ha="left", va="center",
             fontsize=10, color="white", fontweight="bold")
    row_h = 19.6 / max(len(items), 1)
    row_h = min(row_h, 0.95)
    for i, g in enumerate(items):
        y = 19.6 - (i + 1) * row_h
        if i % 2 == 0:
            axR.add_patch(plt.Rectangle((x0, y), w, row_h, facecolor=C_BG, edgecolor="none"))
        axR.text(x0 + 0.012, y + row_h / 2, g["id"], ha="left", va="center",
                 fontsize=8, color=C_MID, fontweight="bold")
        nm = g["name"]
        nm = nm if len(nm) <= 20 else nm[:19] + "…"
        axR.text(x0 + 0.075, y + row_h / 2, nm, ha="left", va="center",
                 fontsize=7.6, color="#222222")
    axR.add_patch(plt.Rectangle((x0, 19.6 - len(items) * row_h), w, (len(items) + 1) * row_h,
                                fill=False, edgecolor=C_DARK, lw=1.0))


guide_col(0.005, 0.5, f"国内指南/共识（{len(dom)} 部）", dom, C_DARK)
guide_col(0.515, 0.48, f"国际指南/共识（{len(intl)} 部）", intl, C_MID)

fig.savefig(OUT, dpi=220, bbox_inches="tight")
plt.close(fig)
print("kg_pipeline_v5 done:", len(dom), "国内 /", len(intl), "国际")
