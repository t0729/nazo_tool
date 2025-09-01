import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# GeoJSON読み込み
gdf = gpd.read_file("input.geojson")

# CRSチェック・セット
if gdf.crs is None:
    gdf.set_crs(epsg=4326, inplace=True)

# nanや無限大の緯度を持つデータがないか確認
if 'geometry' in gdf:
    # centroidの緯度を取り出す
    centroids = gdf.geometry.centroid
    latitudes = centroids.y
    if not np.all(np.isfinite(latitudes)):
        print("緯度に無効な値があります。データを確認してください。")
    
    # 無効データ除去
    gdf = gdf[latitudes.apply(np.isfinite)]

fig, ax = plt.subplots(figsize=(10, 10))
region_col = "region"  # 適宜変更

# 描画処理
if region_col in gdf.columns:
    for region_name, group in gdf.groupby(region_col):
        group.plot(ax=ax, label=region_name, linewidth=1)
else:
    for idx, row in gdf.iterrows():
        row_gdf = gpd.GeoDataFrame([row], crs=gdf.crs)
        row_gdf.plot(ax=ax, label=f"region_{idx}", linewidth=1)

ax.legend()
ax.axis('off')

# SVGファイルとして保存
plt.savefig("output_layers.svg", format="svg", bbox_inches='tight')
plt.close()
