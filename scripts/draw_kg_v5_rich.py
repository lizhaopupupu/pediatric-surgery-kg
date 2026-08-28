# -*- coding: utf-8 -*-
"""kg3.json 点线网络 · 高密度颜色版（16:9）：
- 颜色=疾病归属（tab20），叶子节点同色 + 短标签（碰撞检测防重叠）
- 疾病圆下加指南关键数字注释；边按关系分型（首选/备选/处置/鉴别）
- 共享节点深灰菱形；右侧面板：疾病图例+共享清单+线型图例
输出 kg3_network_rich.{png,svg,pdf}
"""
import json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.executable).parent.parent.parent))
from daimon_runtime import setup_plot
setup_plot()
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
import networkx as nx
from collections import defaultdict
from draw_kg_v3 import SHORT, DIFF_C

ROOT = pathlib.Path(__file__).resolve().parent
kg = json.load(open(ROOT / 'kg5.json', encoding='utf-8'))
N = {n['id']: n for n in kg['nodes']}

DIS_ORDER = ['D002', 'D007', 'D008', 'D009', 'D003', 'D012', 'D006', 'D013',
             'D001', 'D004', 'D005', 'D014', 'D010', 'D011',
             'D015', 'D016', 'D017', 'D018', 'D019', 'D020',
             'D021', 'D022', 'D023', 'D024', 'D025', 'D026']
PAL = list(plt.get_cmap('tab20').colors) + list(plt.get_cmap('tab20b').colors)
DIS_COLOR = {d: PAL[i % len(PAL)] for i, d in enumerate(DIS_ORDER)}
C_SHARED = '#555555'

# 疾病一句话注释（指南关键数字）
NOTE = {
    'D001': '6月龄后手术 · 嵌顿<12h可手法复位',
    'D002': '儿童首选超声→CT/MRI · PAS/AIR评分',
    'D003': '空气灌肠<48h · 成功率>90%',
    'D004': '1岁内观察 · 结扎复发约1.2%',
    'D005': '6-12月龄手术 · 最迟18月龄',
    'D006': '无绞窄先保守70-90%有效 · 72h无效转手术',
    'D007': '压痛不固定 · 多自限',
    'D008': '2%人群2%有症状 · 99mTc显像确诊',
    'D009': '先吐后泻 · ORS为首选',
    'D010': '黄金6小时 · 急诊探查+固定',
    'D011': '女童下腹痛必查附件 · 尽量保卵巢',
    'D012': '胆汁性呕吐=外科急症 · Ladd术',
    'D013': '罗马IV标准 · 聚乙二醇一线',
    'D014': 'Prehn征+ · 先排除扭转',
    'D015': '超声肌层≥4mm · 纠正碱中毒后手术',
    'D016': '活检无神经节细胞确诊 · 警惕HAEC',
    'D017': '60天内葛西手术预后最佳',
    'D018': 'Bell分期 · 气腹即手术',
    'D019': '纽扣电池2小时内急诊内镜',
    'D020': '结肠镜诊断+摘除一体',
    'D021': '2岁内多自闭合 · 观察为主',
    'D022': '区分生理/病理性 · 嵌顿急诊复位',
    'D023': '蓝点征 · 血流正常可保守',
    'D024': '成脓后切开引流 · 约1/3成瘘',
    'D025': '术前必须排除异位甲状腺',
    'D026': 'MRCP首选 · Todani I型最多见',
}


def sname(name, mx=7):
    if name in SHORT:
        return SHORT[name]
    return name if len(name) <= mx else name[:mx - 1] + '…'


# ---------------- 建图 ----------------
DRAW_RELS = {'临床表现', '影像征象', '首选检查', '备选检查', '推荐处置',
             '分型', '并发', '好发部位', '检出手段'}
G = nx.Graph()
for n in kg['nodes']:
    if n['type'] != '指南来源':
        G.add_node(n['id'])
diff_edges, attr_edges = [], []
deg_dis = defaultdict(set)
owner = {}
for e in kg['edges']:
    h, t, r = e['head'], e['tail'], e['relation']
    if h not in G or t not in G:
        continue
    if r == '鉴别诊断':
        diff_edges.append((h, t))
        G.add_edge(h, t, kind='diff')
    elif r in DRAW_RELS:
        G.add_edge(h, t, kind=r)
        attr_edges.append((h, t, r))
        if N[h]['type'] == '疾病' and r != '检出手段':
            deg_dis[t].add(h)

shared = {nid for nid, ds in deg_dis.items() if len(ds) >= 2}
for nid, ds in deg_dis.items():
    if nid not in shared and len(ds) == 1:
        owner[nid] = next(iter(ds))
dis_nmem = defaultdict(int)
for nid, ds in deg_dis.items():
    for d in ds:
        dis_nmem[d] += 1

G_attr = G.edge_subgraph([(h, t) for h, t, d in G.edges(data=True) if d['kind'] != 'diff']).copy()
for nid in G.nodes:
    G_attr.add_node(nid)

# 未与主图连通的子图（如甲状舌管囊肿）加布局用弱虚拟边，防止漂移出画面
hub = 'D002'
for comp in list(nx.connected_components(G_attr)):
    if hub in comp:
        continue
    dis_in_comp = [n for n in comp if N[n]['type'] == '疾病']
    anchor = dis_in_comp[0] if dis_in_comp else next(iter(comp))
    G_attr.add_edge(anchor, hub, weight=0.03)
for h, t in G_attr.edges():
    G_attr[h][t].setdefault('weight', 1.0)

dis_ids = list(DIS_ORDER)
init = {d: (3.2 * math.cos(2 * math.pi * i / len(dis_ids)),
            3.2 * math.sin(2 * math.pi * i / len(dis_ids))) for i, d in enumerate(dis_ids)}
pos = nx.spring_layout(G_attr, pos=init, k=1.6, iterations=800, seed=42, weight='weight')
xs = [p[0] for p in pos.values()]
ys = [p[1] for p in pos.values()]
cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
sc = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
pos = {k: ((v[0] - cx) / sc * 1.25, (v[1] - cy) / sc) for k, v in pos.items()}

# ---------------- 布局参数（供碰撞检测换算） ----------------
AX_W, AX_H = 0.715 * 19.2, 10.8  # 网络区物理尺寸(英寸)
X_HALF, Y_HALF = 1.42, 1.12
UNIT = min(AX_W / (2 * X_HALF), AX_H / (2 * Y_HALF))  # 1 数据单位 ≈ UNIT 英寸
FS_LEAF = 6.3
CH_W = 7.0 / 72 / UNIT          # 单字宽(数据单位)
CH_H = 8.2 / 72 / UNIT          # 行高(数据单位)

# ---------------- 画图 ----------------
fig = plt.figure(figsize=(19.2, 10.8))
ax = fig.add_axes([0.0, 0.0, 0.715, 1.0])
ax.set_aspect('auto')
ax.axis('off')

REL_STYLE = {'首选检查': ('#7A9CC6', 1.7, 'solid'),
             '推荐处置': ('#9BB4D4', 1.3, 'solid'),
             '备选检查': ('#A9BCD6', 1.1, (0, (3, 2))),
             '检出手段': ('#C3D0E4', 0.8, (0, (1, 2)))}
for h, t, r in attr_edges:
    x1, y1 = pos[h]; x2, y2 = pos[t]
    c, lw, ls = REL_STYLE.get(r, ('#D5DEEB', 0.7, 'solid'))
    ax.plot([x1, x2], [y1, y2], color=c, lw=lw, ls=ls, alpha=0.8, zorder=1)
for h, t in diff_edges:
    x1, y1 = pos[h]; x2, y2 = pos[t]
    ax.plot([x1, x2], [y1, y2], color=DIFF_C, lw=1.6, ls=(0, (5, 3)), alpha=0.8, zorder=2)

# ---- 收集标签并做碰撞检测 ----
deg_all = dict(G.degree())
labels = []  # dict: x,y,w,h,text,color,bold,fs
for nid in G.nodes:
    n = N[nid]
    if n['type'] == '疾病':
        continue
    x, y = pos[nid]
    if nid in shared:
        txt = f"◆{sname(n['name'])}×{len(deg_dis[nid])}"
        labels.append(dict(x=x + 0.02, y=y, w=len(txt) * CH_W * 1.15, h=CH_H * 1.2,
                           text=txt, color=C_SHARED, bold=True, fs=7.5, nid=nid))
    else:
        txt = sname(n['name'])
        side = 1 if x >= pos.get(owner.get(nid), (0, 0))[0] else -1
        labels.append(dict(x=x + side * 0.016, y=y, w=len(txt) * CH_W, h=CH_H,
                           text=txt, color='#33465E', bold=False, fs=FS_LEAF,
                           ha='left' if side > 0 else 'right', nid=nid))
for L in labels:
    L.setdefault('ha', 'left')
    if L['ha'] == 'right':
        L['x'] -= L['w']

def overlap(a, b):
    return not (a['x'] + a['w'] < b['x'] or b['x'] + b['w'] < a['x'] or
                a['y'] + a['h'] / 2 < b['y'] - b['h'] / 2 or b['y'] + b['h'] / 2 < a['y'] - a['h'] / 2)

for _ in range(60):
    moved = False
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            a, b = labels[i], labels[j]
            if overlap(a, b):
                push = (min(a['y'] + a['h'] / 2, b['y'] + b['h'] / 2) -
                        max(a['y'] - a['h'] / 2, b['y'] - b['h'] / 2)) / 2 + 0.002
                if a['y'] <= b['y']:
                    a['y'] -= push; b['y'] += push
                else:
                    a['y'] += push; b['y'] -= push
                moved = True
    if not moved:
        break

# ---- 画叶子/共享节点 ----
for nid in G.nodes:
    n = N[nid]
    if n['type'] == '疾病':
        continue
    x, y = pos[nid]
    if nid in shared:
        ax.scatter([x], [y], marker='D', s=150 + 40 * len(deg_dis[nid]), color=C_SHARED,
                   edgecolor='white', lw=1.0, zorder=4)
    else:
        c = DIS_COLOR.get(owner.get(nid), '#999999')
        ax.scatter([x], [y], s=70 + 18 * deg_all[nid], color=c, edgecolor='white',
                   lw=0.7, alpha=0.92, zorder=3)
stroke = [pe.withStroke(linewidth=2.0, foreground='white')]
for L in labels:
    tx = L['x'] if L['ha'] == 'left' else L['x'] + L['w']
    ax.text(tx, L['y'], L['text'], fontsize=L['fs'], color=L['color'],
            fontweight='bold' if L['bold'] else 'normal',
            ha=L['ha'], va='center', zorder=6, path_effects=stroke)

# ---- 疾病节点 + 注释 ----
for d in dis_ids:
    x, y = pos[d]
    c = DIS_COLOR[d]
    ax.scatter([x], [y], s=3400, color=c, edgecolor='white', lw=2.5, zorder=5)
    name = N[d]['name']
    if len(name) > 5:
        h = math.ceil(len(name) / 2)
        nm = name[:h] + '\n' + name[h:]
    else:
        nm = name
    ax.text(x, y, nm, ha='center', va='center', fontsize=11.5, color='white',
            fontweight='bold', zorder=7, linespacing=1.0,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=c)])
    ax.text(x, y - 0.085, NOTE.get(d, ''), ha='center', va='top', fontsize=7.2,
            color='#5A6E8C', zorder=7, path_effects=stroke)

ax.set_xlim(-X_HALF, X_HALF)
ax.set_ylim(-Y_HALF, 1.04)

# 线型图例：网络区左下角横排
lx, ly = -X_HALF + 0.06, -Y_HALF + 0.10
for label, (c, lw, ls) in [('首选检查', REL_STYLE['首选检查']), ('推荐处置', REL_STYLE['推荐处置']),
                            ('备选检查', REL_STYLE['备选检查']), ('鉴别诊断', (DIFF_C, 1.6, (0, (5, 3)))),
                            ('其他关联', ('#D5DEEB', 0.9, 'solid'))]:
    ax.plot([lx, lx + 0.09], [ly, ly], color=c, lw=lw + 0.8, ls=ls, zorder=8)
    ax.text(lx + 0.115, ly, label, fontsize=8, color='#5A6E8C', va='center', zorder=8)
    lx += 0.115 + len(label) * 0.028 + 0.09

# ---------------- 右侧面板 ----------------
axp = fig.add_axes([0.715, 0.0, 0.285, 1.0])
axp.axis('off')
axp.set_xlim(0, 1); axp.set_ylim(0, 1)
axp.add_patch(plt.Rectangle((0, 0.01), 1, 0.98, facecolor='#F4F7FB', edgecolor='#D7E3F4', lw=1.2, zorder=0))


def section(title, yy):
    axp.plot([0.055, 0.055], [yy - 0.011, yy + 0.011], color='#1F4E79', lw=3.5, solid_capstyle='butt')
    axp.text(0.085, yy, title, fontsize=12.5, fontweight='bold', color='#1F4E79', va='center')
    return yy - 0.036


y = section('疾病图例（颜色=归属）', 0.956)
for i, d in enumerate(dis_ids):
    n = N[d]
    col = i // 14           # 左列 14 个，右列 12 个
    row = i % 14
    xx = 0.055 if col == 0 else 0.52
    yy = y - row * 0.0280
    axp.scatter([xx + 0.022], [yy], s=110, color=DIS_COLOR[d], edgecolor='white', lw=1.0, zorder=3)
    nm_leg = n['name'] if len(n['name']) <= 7 else n['name'][:7] + '…'
    axp.text(xx + 0.055, yy, nm_leg, fontsize=8.5, color='#222222', va='center', fontweight='bold')
    axp.text(xx + (0.40 if col == 0 else 0.43), yy, f"{dis_nmem.get(d, 0)}",
             fontsize=8, color='#7C93B8', va='center', ha='right')
y = y - 14 * 0.0280

y -= 0.004
axp.plot([0.05, 0.95], [y, y], color='#D7E3F4', lw=1.2)
y -= 0.012
y = section('跨病种共享节点 TOP10（数字=共享病种数）', y)
shared_top = sorted(shared, key=lambda m: -len(deg_dis[m]))[:10]
for m in shared_top:
    axp.scatter([0.082], [y], marker='D', s=60, color=C_SHARED, zorder=3)
    axp.text(0.130, y, sname(N[m]['name'], 9), fontsize=9.5, color='#333333', va='center')
    axp.text(0.950, y, f"×{len(deg_dis[m])}", fontsize=9.5, color='#7C93B8', va='center', ha='right')
    y -= 0.0245
axp.text(0.130, y, f"…等共 {len(shared)} 个跨病种共享节点", fontsize=9, color='#7C93B8', va='center')
y -= 0.030

y -= 0.004
axp.plot([0.05, 0.95], [y, y], color='#D7E3F4', lw=1.2)
y -= 0.016
axp.text(0.055, y, f"共 {len(kg['nodes'])} 节点 · {len(kg['edges'])} 关系 · 鉴别诊断 {len({tuple(sorted(p)) for p in diff_edges})} 对 · 依据 35 部指南/共识",
         fontsize=9, color='#5A6E8C', va='top')
axp.text(0.055, y - 0.026, '节点明细见 kg5_nodes.csv / kg5_edges.csv，可导入 Neo4j',
         fontsize=9, color='#7C93B8', va='top')

fig.savefig(ROOT / 'kg5_network_rich.png', dpi=200, facecolor='white')
fig.savefig(ROOT / 'kg5_network_rich.svg', facecolor='white')
fig.savefig(ROOT / 'kg5_network_rich.pdf', facecolor='white')
print('done')
