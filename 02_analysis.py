"""
Istanbul mobile speeds around the 5G launch, by district.
Data: Ookla Open Data (CC BY-NC-SA 4.0), mobile tiles, quarterly.
Boundaries: geoBoundaries gbOpen TUR ADM2 (OpenStreetMap-derived, ODbL).
Run:  python3 02_analysis.py
"""
import json, unicodedata, duckdb, pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ISTANBUL = """adalar arnavutkoy atasehir avcilar bagcilar bahcelievler bakirkoy basaksehir bayrampasa besiktas beykoz
beylikduzu beyoglu buyukcekmece catalca cekmekoy esenler esenyurt eyupsultan eyup fatih gaziosmanpasa gungoren kadikoy kagithane
kartal kucukcekmece maltepe pendik sancaktepe sariyer silivri sultanbeyli sultangazi sile sisli tuzla umraniye uskudar zeytinburnu""".split()
def norm(s):
    s = s.replace("ı","i").replace("İ","i")
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return "".join(c for c in s if c.isalpha())
LON0, LON1, LAT0, LAT1 = 27.95, 29.95, 40.80, 41.60

gj = json.load(open("boundaries/tur_adm2.geojson"))
dist = []
for f in gj["features"]:
    g = shape(f["geometry"]); c = g.centroid
    if LON0 <= c.x <= LON1 and LAT0 <= c.y <= LAT1 and norm(f["properties"]["shapeName"]) in ISTANBUL:
        n = norm(f["properties"]["shapeName"]); n = "eyupsultan" if n == "eyup" else n
        dist.append((f["properties"]["shapeName"], n, g))
names = {d[1] for d in dist}
print(f"matched {len(dist)} polygons / {len(names)} distinct names; missing:", sorted(set(ISTANBUL)-names-{'eyup'}))

geoms = [d[2] for d in dist]; tree = STRtree(geoms)
QS = [(2025,1),(2025,2),(2025,3),(2025,4),(2026,1),(2026,2),(2026,3)]
con = duckdb.connect()
frames = []
for y,q in QS:
    df = con.execute(f"SELECT tile_x,tile_y,avg_d_kbps,avg_u_kbps,avg_lat_ms,tests FROM read_parquet('data/istanbul_{y}_q{q}.parquet')").df()
    df["period"] = f"{y}Q{q}"; frames.append(df)
t = pd.concat(frames, ignore_index=True)

# assign each unique tile centre to a district (point in polygon)
pts = t[["tile_x","tile_y"]].drop_duplicates().reset_index(drop=True)
def find(r):
    p = Point(r.tile_x, r.tile_y)
    for i in tree.query(p, predicate="within"):
        return dist[i][1]
    return None
pts["district"] = pts.apply(find, axis=1)
t = t.merge(pts, on=["tile_x","tile_y"], how="left")
print(f"tiles assigned to a district: {t.district.notna().mean():.1%}")
t = t.dropna(subset=["district"])

t["dl_x_tests"] = t.avg_d_kbps * t.tests
g = t.groupby(["district","period"]).agg(tests=("tests","sum"), dl_x=("dl_x_tests","sum"), tiles=("tests","size")).reset_index()
g["dl_mbps"] = g.dl_x / g.tests / 1000
wide = g.pivot(index="district", columns="period", values="dl_mbps")
tests = g.pivot(index="district", columns="period", values="tests")
out = wide.round(1).copy()
out["base_2025_mean"] = wide[["2025Q1","2025Q2","2025Q3","2025Q4"]].mean(axis=1).round(1)
out["x_2026Q2_vs_2025Q4"] = (wide["2026Q2"]/wide["2025Q4"]).round(2)
out["x_2026Q1_vs_2025Q4"] = (wide["2026Q1"]/wide["2025Q4"]).round(2)
out["min_tests"] = tests.min(axis=1)
out.to_csv("district_results.csv")
print(out.sort_values("x_2026Q2_vs_2025Q4").to_string())
