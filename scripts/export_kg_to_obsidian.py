# -*- coding: utf-8 -*-
"""把 kg3.json 知识图谱导出为 Obsidian 笔记库。
每个节点一篇 Markdown 笔记，关系转 [[双链]]，类型转 tag（图谱视图可按 tag 分组配色）。
输出：output/小儿外科KG-Obsidian/，可直接作为 Obsidian vault 打开。
"""
import json
import re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / "output" / "小儿外科KG-Obsidian"

kg = json.load(open(BASE / "knowledge_graph" / "kg5.json", encoding="utf-8"))
nodes = kg["nodes"]
edges = kg["edges"]

ILLEGAL = r'[\\/:*?"<>|]'


def safe(name):
    return re.sub(ILLEGAL, "_", name).strip()


by_id = {n["id"]: n for n in nodes}
# 同名冲突检测
name_count = defaultdict(int)
for n in nodes:
    name_count[n["name"]] += 1

folders = {"疾病": "01 疾病", "检查手段": "02 检查手段", "影像征象": "03 影像征象",
           "临床表现": "04 临床表现", "分型": "05 分型", "处置": "06 处置",
           "并发症": "07 并发症", "解剖部位": "08 解剖部位", "指南来源": "09 指南来源"}

# 节点 -> 笔记相对路径（无扩展名），供双链使用
note_path = {}
for n in nodes:
    fname = safe(n["name"])
    if name_count[n["name"]] > 1:
        fname = f"{fname}（{n['type']}）"
    folder = folders.get(n["type"], "99 其他")
    note_path[n["id"]] = f"{folder}/{fname}"

# 每个节点的出边，按关系分组
out_edges = defaultdict(lambda: defaultdict(list))
for e in edges:
    out_edges[e["head"]][e["relation"]].append(e)


def render_node(n):
    lines = ["---"]
    lines.append(f"kg_id: {n['id']}")
    lines.append(f"type: {n['type']}")
    if n.get("code"):
        lines.append(f"code: \"{n['code']}\"")
    lines.append(f"tags:")
    lines.append(f"  - {n['type']}")
    syn = n.get("props", {}).get("同义词")
    if syn:
        lines.append("aliases:")
        for a in re.split(r"[;；]", syn):
            a = a.strip()
            if a:
                lines.append(f"  - \"{a}\"")
    lines.append("---")
    lines.append("")
    lines.append(f"# {n['name']}")
    lines.append("")

    props = {k: v for k, v in n.get("props", {}).items() if k != "同义词"}
    if props:
        lines.append("## 属性")
        lines.append("")
        for k, v in props.items():
            lines.append(f"- **{k}**：{v}")
        lines.append("")

    rels = out_edges.get(n["id"], {})
    if rels:
        lines.append("## 关系")
        lines.append("")
        for rel, es in rels.items():
            lines.append(f"### {rel}")
            for e in es:
                tgt = by_id.get(e["tail"])
                if not tgt:
                    continue
                link = note_path[e["tail"]]
                item = f"- [[{link}|{tgt['name']}]]"
                attrs = e.get("attributes") or {}
                for ak, av in attrs.items():
                    item += f"　（{ak}：{av}）"
                lines.append(item)
            lines.append("")
    return "\n".join(lines)


count = 0
for n in nodes:
    p = OUT / (note_path[n["id"]] + ".md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_node(n), encoding="utf-8")
    count += 1

# 总览 MOC
n_dis = sum(1 for n in nodes if n["type"] == "疾病")
n_gui = sum(1 for n in nodes if n["type"] == "指南来源")
moc = ["---", "type: MOC", "tags:", "  - 总览", "---", "",
       "# 小儿外科鉴别诊断知识图谱 v0.5", "",
       f"共 **{len(nodes)} 个节点 / {len(edges)} 条关系**，{n_dis} 个病种，依据 {n_gui} 部指南/专家共识构建。", "",
       "## 疾病", ""]
for n in nodes:
    if n["type"] == "疾病":
        moc.append(f"- [[{note_path[n['id']]}|{n['name']}]]")
moc += ["", "## 指南来源", ""]
for n in nodes:
    if n["type"] == "指南来源":
        moc.append(f"- [[{note_path[n['id']]}|{n['name']}]]")
moc += ["", "---", "",
        "> 使用提示：打开图谱视图（Graph View）后，可按 tag 设置分组配色，",
        "> 例如 `tag:#疾病` 一组颜色、`tag:#检查手段` 一组颜色。", ""]
(OUT / "00 知识图谱总览.md").write_text("\n".join(moc), encoding="utf-8")

print(f"生成 {count} 篇笔记 + 总览，输出到 {OUT}")
