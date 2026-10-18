"""Sanity check: do other cities show the same Q1 2026 jump as Istanbul? (If yes, suspect a data/method change.)"""
import duckdb, threading, json
B="https://ookla-open-data.s3.us-west-2.amazonaws.com/parquet/performance/type=mobile"
S={1:"01-01",2:"04-01",3:"07-01",4:"10-01"}
Q=[(2025,3),(2025,4),(2026,1),(2026,2),(2026,3)]
CITIES={"Istanbul":(27.95,29.95,40.80,41.60),"Ankara":(32.5,33.1,39.7,40.1),"Izmir":(26.9,27.4,38.3,38.6),
        "Athens":(23.5,24.1,37.8,38.2),"Berlin":(13.1,13.8,52.3,52.7),"Bucharest":(25.9,26.3,44.3,44.6)}
res={}
def work(y,q):
    con=duckdb.connect(); con.execute("INSTALL httpfs; LOAD httpfs;")
    u=f"{B}/year={y}/quarter={q}/{y}-{S[q]}_performance_mobile_tiles.parquet"
    sel=", ".join(f"sum(CASE WHEN tile_x BETWEEN {a} AND {b} AND tile_y BETWEEN {c} AND {d} THEN avg_d_kbps*tests END)/nullif(sum(CASE WHEN tile_x BETWEEN {a} AND {b} AND tile_y BETWEEN {c} AND {d} THEN tests END),0)/1000 AS \"{n}_mbps\", sum(CASE WHEN tile_x BETWEEN {a} AND {b} AND tile_y BETWEEN {c} AND {d} THEN tests END) AS \"{n}_tests\"" for n,(a,b,c,d) in CITIES.items())
    r=con.execute(f"SELECT {sel} FROM read_parquet('{u}')").fetchone()
    res[f"{y}Q{q}"]=r
ths=[threading.Thread(target=work,args=a) for a in Q]
[t.start() for t in ths]; [t.join() for t in ths]
names=list(CITIES)
print("city        "+"  ".join(f"{k:>8}" for k in sorted(res)))
for i,n in enumerate(names):
    print(f"{n:<11} "+"  ".join(f"{res[k][2*i]:8.1f}" for k in sorted(res))+"   Mbps")
for i,n in enumerate(names):
    print(f"{n:<11} "+"  ".join(f"{int(res[k][2*i+1]):8d}" for k in sorted(res))+"   tests")
