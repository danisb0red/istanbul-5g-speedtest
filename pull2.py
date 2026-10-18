import duckdb, os, sys, time, threading
B="https://ookla-open-data.s3.us-west-2.amazonaws.com/parquet/performance/type=mobile"
S={1:"01-01",2:"04-01",3:"07-01",4:"10-01"}
Q=[(2025,1),(2025,2),(2025,3),(2025,4),(2026,1),(2026,2),(2026,3)]
LON0,LON1,LAT0,LAT1=27.95,29.95,40.80,41.60
os.makedirs("data",exist_ok=True)
def work(y,q):
    out=f"data/istanbul_{y}_q{q}.parquet"
    if os.path.exists(out): print("have",out,flush=True); return
    t=time.time()
    con=duckdb.connect(); con.execute("LOAD httpfs") if False else con.execute("INSTALL httpfs; LOAD httpfs;")
    u=f"{B}/year={y}/quarter={q}/{y}-{S[q]}_performance_mobile_tiles.parquet"
    tmp=out+".tmp"
    con.execute(f"""COPY (SELECT quadkey,tile_x,tile_y,avg_d_kbps,avg_u_kbps,avg_lat_ms,tests,devices
      FROM read_parquet('{u}') WHERE tile_x BETWEEN {LON0} AND {LON1} AND tile_y BETWEEN {LAT0} AND {LAT1})
      TO '{tmp}' (FORMAT PARQUET)""")
    os.rename(tmp,out)
    n=con.execute(f"select count(*) from read_parquet('{out}')").fetchone()[0]
    print("done",y,q,n,"rows",round(time.time()-t),"s",flush=True)
ths=[threading.Thread(target=work,args=a) for a in Q]
[t.start() for t in ths]; [t.join() for t in ths]
print("FINISHED",flush=True)
