# -*- coding: utf-8 -*-
"""
点位表转 GeoJSON：读含 城市 / 经度 / 纬度 列的 CSV，校验坐标，可选做 WGS84 与 GCJ-02 互转，
输出 GeoJSON，可选出散点图。

用法：
    python points.py --input cities.csv --output points.geojson
    python points.py --input cities.csv --convert wgs2gcj --map
"""
import argparse

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from coord_transform import gcj02_to_wgs84, wgs84_to_gcj02
from _caption import add_caption

plt.rcParams["font.family"] = ["Times New Roman", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

REQUIRED = ["城市", "经度", "纬度"]


def main() -> int:
    p = argparse.ArgumentParser(description="点位表转 GeoJSON")
    p.add_argument("--input", required=True, help="输入 CSV（含 城市、经度、纬度 列）")
    p.add_argument("--output", default="points.geojson")
    p.add_argument("--convert", choices=["none", "wgs2gcj", "gcj2wgs"], default="none")
    p.add_argument("--map", action="store_true", help="同时输出散点图 points_map.png")
    args = p.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要字段：{missing}")

    df["经度"] = pd.to_numeric(df["经度"], errors="coerce")
    df["纬度"] = pd.to_numeric(df["纬度"], errors="coerce")
    valid = (df["经度"].notna() & df["纬度"].notna()
             & df["经度"].between(-180, 180) & df["纬度"].between(-90, 90))
    print(f"原始记录数：{len(df)}")
    print(f"无效记录数：{int((~valid).sum())}")
    df = df.loc[valid].copy()

    if args.convert != "none":
        fn = wgs84_to_gcj02 if args.convert == "wgs2gcj" else gcj02_to_wgs84
        coords = df.apply(lambda r: fn(r["经度"], r["纬度"]), axis=1)
        df["经度"] = [c[0] for c in coords]
        df["纬度"] = [c[1] for c in coords]
        print(f"坐标转换：{args.convert}")

    geometry = gpd.points_from_xy(df["经度"], df["纬度"])
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    # pandas 3 的 str 扩展类型 GeoJSON 驱动不认，统一转回 object
    for c in gdf.columns:
        if c != "geometry" and str(gdf[c].dtype).startswith("str"):
            gdf[c] = gdf[c].astype(object)
    gdf.to_file(args.output, driver="GeoJSON", encoding="utf-8")
    print(f"有效记录数：{len(gdf)}；坐标系：{gdf.crs}；输出：{args.output}")

    if args.map:
        fig = plt.figure(figsize=(8.27, 5.5), facecolor="white")
        ax = fig.add_axes([0.08, 0.26, 0.84, 0.66])
        ax.set_facecolor("white")
        ax.axis("off")
        gdf.plot(ax=ax, markersize=10, color="#C0392B", edgecolor="white", linewidth=0.4)
        mnx, mny, mxx, mxy = gdf.total_bounds
        pad = max((mxx - mnx), (mxy - mny)) * 0.08 or 0.01
        x0, x1 = mnx - pad, mxx + pad
        y0, y1 = mny - pad, mxy + pad
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect(1)
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                               edgecolor="#9AA6B2", linewidth=0.8, zorder=6))
        add_caption(fig, 1, "点位分布",
                    [f"共 {len(gdf)} 个点，坐标为 {args.convert} 转换后的经纬度",
                     "坐标系 WGS 84（EPSG:4326），图面按经纬度等比例",
                     "本图为示意性分布图，无审图号，非标准地图"],
                    lb=0.08, rb=0.92, pad=0.40, gap=0.10)
        plt.savefig("points_map.png", dpi=300, facecolor="white")
        plt.close(fig)
        print("散点图：points_map.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
