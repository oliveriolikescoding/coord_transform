# -*- coding: utf-8 -*-
"""
西南四城市人口分布图（示例数据）。

读 cities.geojson 的点位（城市、经度、纬度、人口，单位万人）与 四川省.geojson 的市级界线，
按人口平方根定气泡半径出图。版式按 RV-16 排：图内不放标题与图号块，图号与题名置图下。

用法：
    python make_map.py      # 输出 cities_map.png（300 dpi）
"""
import math

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib import patheffects

from _caption import add_caption

plt.rcParams["font.family"] = ["Times New Roman", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

POINTS = "cities.geojson"
BASEMAP = "四川省.geojson"
OUT = "cities_map.png"
DPI = 300

cities = gpd.read_file(POINTS)
base = gpd.read_file(BASEMAP)

fig = plt.figure(figsize=(11.69, 8.27), facecolor="white")
ax = fig.add_axes([0.075, 0.235, 0.85, 0.68])
ax.set_facecolor("white")
ax.axis("off")

base.plot(ax=ax, facecolor="#F2F4F7", edgecolor="#AEB9C4", linewidth=0.7, zorder=1)
cities.plot(ax=ax, color="#C0392B", markersize=6, zorder=3)

minx, miny, maxx, maxy = base.total_bounds
cb = cities.total_bounds
minx, miny = min(minx, cb[0]), min(miny, cb[1])
maxx, maxy = max(maxx, cb[2]), max(maxy, cb[3])
mid_lat = (miny + maxy) / 2
ax.set_aspect(1 / math.cos(math.radians(mid_lat)))
pad = 0.03
x0, x1 = minx - (maxx - minx) * pad, maxx + (maxx - minx) * pad
y0, y1 = miny - (maxy - miny) * pad, maxy + (maxy - miny) * pad
ax.set_xlim(x0, x1)
ax.set_ylim(y0, y1)
W, H = x1 - x0, y1 - y0

# 气泡：半径按人口平方根定，单位取图面数据坐标
pop = cities["人口"].astype(float)
r_max = W * 0.018
for _, row in cities.iterrows():
    x, y = row.geometry.x, row.geometry.y
    r = r_max * math.sqrt(row["人口"] / pop.max())
    ax.add_patch(plt.Circle((x, y), r, facecolor="#C0392B", alpha=0.55,
                            edgecolor="#7B241C", linewidth=0.6, zorder=3))
    ax.annotate(f"{row['城市']} {row['人口']:,.0f}",
                xy=(x, y), xytext=(x + r + W * 0.006, y + r * 0.7),
                ha="left", va="center", fontsize=7.6, color="#1a1a1a", zorder=4,
                path_effects=[patheffects.withStroke(linewidth=2.0, foreground="white")])

# 图廓
for inset, lw in ((0.0, 0.9), (0.007, 0.35)):
    ax.add_patch(Rectangle((inset, inset), 1 - 2 * inset, 1 - 2 * inset,
                           transform=ax.transAxes, fill=False, edgecolor="#9AA6B2",
                           linewidth=lw, zorder=6, clip_on=False))

# 经纬度注记
sx = 2.0 if W / 2.0 <= 7 else 3.0
sy = 1.0 if H <= 7 else 2.0
for v in [x for x in (96, 98, 100, 102, 104, 106, 108, 110) if x0 < x < x1]:
    ax.text(v, y0 - H * 0.012, f"{v}°", ha="center", va="top",
            fontsize=6.4, color="#4A5A6A", clip_on=False)
for v in [y for y in (26, 28, 30, 32, 34) if y0 < y < y1]:
    ax.text(x0 - W * 0.010, v, f"{v}°", ha="right", va="center",
            fontsize=6.4, color="#4A5A6A", clip_on=False)

# 指北针（图廓内右上，贴顶边）
nx, ny = 0.955, 0.955
ax.add_patch(Polygon([[nx, ny - 0.028], [nx - 0.010, ny - 0.082],
                      [nx, ny - 0.066], [nx + 0.010, ny - 0.082]],
                     closed=True, transform=ax.transAxes, facecolor="#243447",
                     edgecolor="none", zorder=7))
ax.text(nx, ny - 0.019, "N", transform=ax.transAxes, ha="center", va="top",
        fontsize=7.6, color="#243447", zorder=7)

# 比例尺（按中心纬度换算）
km_per_deg = 111.32 * math.cos(math.radians(mid_lat))
bar_km = 200.0
bar_deg = bar_km / km_per_deg
bx, by = x0 + W * 0.030, y0 + H * 0.030
bh = H * 0.008
for i in range(4):
    ax.add_patch(Rectangle((bx + i * bar_deg / 4, by), bar_deg / 4, bh,
                           facecolor="#243447" if i % 2 == 0 else "#FFFFFF",
                           edgecolor="#243447", linewidth=0.5, zorder=7))
for frac, txt, ha in ((0, "0", "center"), (0.5, f"{bar_km / 2:g}", "center"),
                      (1, f"{bar_km:g} km", "right")):
    ax.text(bx + bar_deg * frac, by + bh * 2.6, txt, ha=ha, va="bottom",
            fontsize=6.6, color="#243447", zorder=7)

caption_title = "西南四城市人口分布（示例数据）"
notes = [
    f"共 {len(cities)} 个城市，气泡半径按人口平方根定，标注值为常住人口（万人）",
    "点位坐标为城市中心经纬度，取自 cities.geojson 的 经度、纬度 字段",
    "底图为四川省市级行政界线，DataV.GeoAtlas，仅作空间参照，非法定界线",
    "投影为地理坐标（WGS 84 经纬度），比例尺按中心纬度 "
    f"{mid_lat:.1f}° 换算，1° 经差约 {km_per_deg:.0f} km",
    "图中城市含重庆市（市域口径），不在四川省界线范围内，仅作相对位置参照",
    "本图为示意性专题图，无审图号，非标准地图",
]
add_caption(fig, 1, caption_title, notes, lb=0.055, rb=0.945, pad=0.45, gap=0.10)

plt.savefig(OUT, dpi=DPI, facecolor="white")
plt.close(fig)
print(f"✅ 完成：{OUT}（{DPI} dpi）")


