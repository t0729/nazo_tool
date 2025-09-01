import csv

# 4分の1地域メッシュコードを計算する関数
def latlon_to_meshcode(lat, lon):
    # 参考: PostgreSQLの式をPythonに変換
    lat60 = lat * 60
    lon60 = lon * 60
    part1 = int(lat60 // 40)
    part2 = int(lon - 100)
    part3 = int((lat60 % 40) // 5)
    part4 = int((lon60 % 60) // 7.5)
    part5 = int(((lat60 % 40) % 5 * 60) // 30)
    part6 = int(((lon60 % 60) % 7.5 * 60) // 45)
    part7 = int((((lat60 % 40) % 5 * 60) % 30) // 15) * 2 + int((((lon60 % 60) % 7.5 * 60) % 45) // 22.5) + 1
    part8 = int(((((lat60 % 40) % 5 * 60) % 30) % 15) // 7.5) * 2 + int(((((lon60 % 60) % 7.5 * 60) % 45) % 22.5) // 11.25) + 1

    meshcode = f"{part1}{part2}{part3}{part4}{part5}{part6}{part7}{part8}"
    return meshcode

# CSVファイルからARV辞書を作成
def load_arv_dict(csv_path):
    arv_dict = {}
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        for line in csvfile:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # 空行やコメント行は読み飛ばす
            row = [x.strip() for x in line.split(",")]
            if len(row) < 4:
                continue  # 要素が足りなければスキップ
            meshcode = row[0]
            arv = row[3]
            arv_dict[meshcode] = arv
    return arv_dict

# 周辺メッシュコード8方向(縦横斜め)を生成
def get_neighbor_meshcodes(meshcode):
    # meshcodeは文字列11桁（4分の1地域は10桁だけど拡張11桁でも対応可能）
    # メッシュコードの構造上、ここではとりあえず末尾1桁の +1/-1を試すだけ簡易例
    neighbors = []
    base = meshcode[:-1]
    last_digit = int(meshcode[-1])
    for delta in [-1, 0, 1]:
        for delta2 in [-1, 0, 1]:
            if delta == 0 and delta2 == 0:
                continue
            # ここは本当は緯度経度でオフセット計算した方が良いけど
            # とりあえず末尾の数字を +- 1 しただけの例（実務には要修正）
            new_last = last_digit + delta + delta2
            if 1 <= new_last <= 4:
                neighbors.append(base + str(new_last))
    return neighbors

# ARV値が0.0000なら周辺から補完する処理
def get_arv_with_neighbors(meshcode, arv_dict):
    arv = arv_dict.get(meshcode, "0.0000")
    if arv == "0.0000" or arv == "0":
        neighbors = get_neighbor_meshcodes(meshcode)
        for nb in neighbors:
            arv_nb = arv_dict.get(nb, None)
            if arv_nb and arv_nb != "0.0000" and arv_nb != "0":
                return arv_nb
        return "1"  # それでも見つからなければ1を返す
    return arv

def main():
    arv_csv = "Z-V4-JAPAN-AMP-VS400_M250.csv"  # ARV値CSVのパス
    lat_file = "lat.txt"
    lon_file = "lon.txt"
    output_file = "output_arv.txt"

    # ARV辞書読み込み
    arv_dict = load_arv_dict(arv_csv)

    # 緯度経度読み込み
    with open(lat_file, "r", encoding="utf-8") as f_lat, open(lon_file, "r", encoding="utf-8") as f_lon:
        lats = [float(line.strip()) for line in f_lat]
        lons = [float(line.strip()) for line in f_lon]

    coords = list(zip(lats, lons))

    with open(output_file, "w", encoding="utf-8") as out:
        for lat, lon in coords:
            meshcode = latlon_to_meshcode(lat, lon)
            arv = get_arv_with_neighbors(meshcode, arv_dict)
            out.write(f"{lat},{lon},{meshcode},{arv}\n")

if __name__ == "__main__":
    main()
