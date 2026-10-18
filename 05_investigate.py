"""Why does Istanbul's Ookla speed jump in Q1 2026? Diagnostics on tile composition and test volumes."""
import duckdb, pandas as pd
pd.set_option("display.width",200)
con=duckdb.connect()
Q=[(2025,3),(2025,4),(2026,1),(2026,2),(2026,3)]
con.execute("CREATE VIEW t AS "+" UNION ALL ".join(f"SELECT '{y}Q{q}' AS p,* FROM read_parquet('data/istanbul_{y}_q{q}.parquet')" for y,q in Q))
print("== 1. Speed distribution of tiles (Mbps) ==")
print(con.execute("""SELECT p, round(quantile_cont(avg_d_kbps,0.5)/1000) p50, round(quantile_cont(avg_d_kbps,0.9)/1000) p90,
 round(quantile_cont(avg_d_kbps,0.99)/1000) p99, round(max(avg_d_kbps)/1000) mx,
 round(avg((avg_d_kbps>300000)::int),3) share_gt300 FROM t GROUP BY p ORDER BY p""").df().to_string(index=False))
print("\n== 4. Same tiles only (matched by quadkey) ==")
for a,b in [("2025Q4","2026Q1"),("2026Q1","2026Q2"),("2025Q4","2026Q3")]:
    r=con.execute(f"""SELECT count(*) n, round(avg(x.avg_d_kbps)/1000,1) mean_a, round(avg(y.avg_d_kbps)/1000,1) mean_b,
      round(median(y.avg_d_kbps-x.avg_d_kbps)/1000,1) median_change, round(avg((y.avg_d_kbps>x.avg_d_kbps)::int),2) share_improved
      FROM t x JOIN t y USING(quadkey) WHERE x.p='{a}' AND y.p='{b}'""").fetchone()
    print(a,"->",b,"n,mean_a,mean_b,median_change,share_improved =",r)
print("\n== 5. Tiles new in 2026Q1 vs tiles that already existed in 2025Q4 ==")
print(con.execute("""SELECT (quadkey IN (SELECT quadkey FROM t WHERE p='2025Q4')) AS existed_2025Q4, count(*) tiles, sum(tests) tests,
 round(sum(avg_d_kbps*tests)/sum(tests)/1000,1) mbps FROM t WHERE p='2026Q1' GROUP BY 1""").df().to_string(index=False))
print("\n== 6. Mixture arithmetic for Q1 2026 ==")
b=con.execute("SELECT sum(tests), sum(avg_d_kbps*tests)/sum(tests)/1000 FROM t WHERE p='2025Q4'").fetchone()
q=con.execute("SELECT sum(tests), sum(avg_d_kbps*tests)/sum(tests)/1000 FROM t WHERE p='2026Q1'").fetchone()
extra=q[0]-b[0]; implied=(q[0]*q[1]-b[0]*b[1])/extra
print(f"Q4'25: {b[0]:.0f} tests at {b[1]:.0f} Mbps; Q1'26: {q[0]:.0f} tests at {q[1]:.0f} Mbps")
print(f"If the Q4 volume ran at the Q4 speed, the {extra:.0f} extra Q1 tests would have averaged {implied:.0f} Mbps")
