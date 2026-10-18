import json, unicodedata, duckdb, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import PatchCollection
from shapely.geometry import shape
INK, MUTED, GRID, BLUE = "#1f2933", "#6b7785", "#e4e8ec", "#1d5fa8"
plt.rcParams.update({"font.family":"DejaVu Sans","axes.edgecolor":GRID,"axes.labelcolor":MUTED,"xtick.color":MUTED,"ytick.color":MUTED})

# ---------- Figure 1: citywide timeline + sample size ----------
QS=[(2025,1),(2025,2),(2025,3),(2025,4),(2026,1),(2026,2),(2026,3)]
con=duckdb.connect()
rows=[]
for y,q in QS:
    r=con.execute(f"SELECT sum(avg_d_kbps*tests)/sum(tests)/1000, sum(tests) FROM read_parquet('data/istanbul_{y}_q{q}.parquet')").fetchone()
    rows.append((f"{y} Q{q}",r[0],r[1]))
df=pd.DataFrame(rows,columns=["q","dl","tests"])
fig,(a1,a2)=plt.subplots(2,1,figsize=(8,6.2),gridspec_kw={"height_ratios":[3,1.3]},sharex=True)
a1.plot(df.q,df.dl,color=BLUE,lw=2,marker="o",ms=7,mfc=BLUE,mec="white",mew=2,zorder=3)
for i,(q,v) in enumerate(zip(df.q,df.dl)):
    a1.annotate(f"{v:.0f}",(i,v),textcoords="offset points",xytext=(0,10),ha="center",color=INK,fontsize=10)
a1.axvline(4.5,color=MUTED,lw=1,ls=(0,(4,3)))
a1.text(4.55,30,"Official 5G launch\n1 April 2026",color=MUTED,fontsize=9,va="bottom")
a1.set_ylim(0,330); a1.set_ylabel("Mbps (test-weighted mean download)")
a1.set_title("Istanbul mobile speeds jumped in Q1 2026, before the 1 April launch",loc="left",color=INK,fontsize=11.5,fontweight="bold",pad=14)
a1.grid(axis="y",color=GRID,lw=1); a1.set_axisbelow(True)
for s in ("top","right"): a1.spines[s].set_visible(False)
a2.bar(df.q,df.tests/1000,color="#9db8d6",width=0.55)
a2.set_ylabel("Speedtests\n(thousands)"); a2.grid(axis="y",color=GRID,lw=1); a2.set_axisbelow(True)
for s in ("top","right"): a2.spines[s].set_visible(False)
fig.text(0.01,0.005,"Source: Ookla Open Data (CC BY-NC-SA 4.0), mobile tiles within an Istanbul bounding box. Quarterly data cannot date the jump within Q1.",fontsize=7.5,color=MUTED)
fig.tight_layout(rect=(0,0.02,1,1)); fig.savefig("fig1_timeline.png",dpi=200); plt.close(fig)

# ---------- Figure 2: district maps, before vs after ----------
def norm(s):
    s=s.replace("ı","i").replace("İ","i")
    return "".join(c for c in unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower() if c.isalpha())
res=pd.read_csv("district_results.csv").set_index("district")
gj=json.load(open("boundaries/tur_adm2.geojson"))
polys=[]
for f in gj["features"]:
    n=norm(f["properties"]["shapeName"]); n="eyupsultan" if n=="eyup" else n
    g=shape(f["geometry"]); c=g.centroid
    if n in res.index and 27.95<=c.x<=29.95 and 40.8<=c.y<=41.6: polys.append((n,g))
vmin,vmax=50,400
fig,axs=plt.subplots(1,2,figsize=(11,4.4))
cmap=plt.get_cmap("Blues")
for ax,col,title in zip(axs,["2025Q4","2026Q2"],["Q4 2025 (before 5G)","Q2 2026 (after launch)"]):
    patches,vals=[],[]
    for n,g in polys:
        for part in (g.geoms if g.geom_type=="MultiPolygon" else [g]):
            patches.append(MPoly(list(part.exterior.coords))); vals.append(res.loc[n,col])
    pc=PatchCollection(patches,cmap=cmap,edgecolor="white",linewidth=0.5); pc.set_array(pd.Series(vals).clip(vmin,vmax).values); pc.set_clim(vmin,vmax)
    ax.add_collection(pc); ax.set_xlim(27.95,29.95); ax.set_ylim(40.80,41.60); ax.set_aspect(1.3); ax.axis("off")
    ax.set_title(title,color=INK,fontsize=11,loc="left")
cb=fig.colorbar(pc,ax=axs,shrink=0.7,pad=0.02); cb.set_label("Mbps (test-weighted mean download, by district)",color=MUTED)
fig.suptitle("Before, Istanbul's districts ranged from slow to fast. After, almost all moved up.",x=0.02,y=1.0,ha="left",color=INK,fontsize=12,fontweight="bold")
fig.text(0.02,0.01,"Source: Ookla Open Data (CC BY-NC-SA 4.0); district polygons: geoBoundaries gbOpen (OSM, ODbL). Adalar not matched; ~13% of tiles fell outside matched districts.",fontsize=7.5,color=MUTED)
fig.savefig("fig2_district_maps.png",dpi=200,bbox_inches="tight"); plt.close(fig)
print("ok")
