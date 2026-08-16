#!/usr/bin/env python3
"""Generate UNWEIGHTED within-TPU alternative origin points for an origin-sensitivity re-route.
NOT population-weighted (no sub-TPU population data exist). Produces an interior grid of
points per TPU, always including a guaranteed-interior representative point.
Run in the project's Python env (geopandas required). Reads frozen geometry; writes only a new CSV."""
import geopandas as gpd, numpy as np, pandas as pd
from pathlib import Path
from shapely.geometry import Point
ROOT = Path(__file__).resolve().parents[3]
generated_inputs = ROOT/"analysis/stage9a/inputs"
frozen_inputs = ROOT/"reference_outputs/stage9a/inputs"
input_dir = generated_inputs if (generated_inputs/"tpu_geography_v3.gpkg").exists() else frozen_inputs
gdf = gpd.read_file(input_dir/"tpu_geography_v3.gpkg")
frozen_origins = pd.read_csv(input_dir/"tpu_origins_v3.csv", dtype={"id": str})
ALT_ROOT = ROOT/"analysis/stage9a/alt_origin_runs"
INPUT_DIR = ALT_ROOT/"inputs"
INPUT_DIR.mkdir(parents=True, exist_ok=True)
# identify TPU id column
idcol = next(c for c in gdf.columns if c.lower() in ("id","tpu","tpu_id","area_id"))
gdf = gdf.to_crs(4326)
GRID = 3  # up to GRID*GRID interior candidate points per TPU
rows=[]
for _,r in gdf.iterrows():
    tid=str(r[idcol]); poly=r.geometry
    if poly is None or poly.is_empty: continue
    rp=poly.representative_point(); rows.append((rp.x, rp.y, tid, "representative_point"))
    minx,miny,maxx,maxy=poly.bounds
    xs=np.linspace(minx,maxx,GRID+2)[1:-1]; ys=np.linspace(miny,maxy,GRID+2)[1:-1]
    k=0
    for x in xs:
        for y in ys:
            p=Point(x,y)
            if poly.contains(p):
                rows.append((x, y, tid, "interior_grid")); k+=1
out_alt=pd.DataFrame(rows, columns=["lon","lat","tpu_id","origin_type"])
# Avoid giving an accidental duplicate point extra weight in the TPU mean.
out_alt=out_alt.drop_duplicates(["tpu_id","lon","lat"], keep="first").copy()
out_alt["point_index"]=out_alt.groupby("tpu_id").cumcount()
out_alt["id"]=out_alt["tpu_id"].astype(str)+"__p"+out_alt["point_index"].astype(str)
out_alt=out_alt[["id","lon","lat","tpu_id","origin_type"]]

# Re-route the original frozen centroid as a guard candidate. It is included in
# the sampled best-case but excluded from the alternative-point mean-case.
centroids=frozen_origins.rename(columns={"id":"tpu_id"}).copy()
centroids["id"]=centroids["tpu_id"].astype(str)+"__centroid"
centroids["origin_type"]="frozen_centroid"
centroids=centroids[["id","lon","lat","tpu_id","origin_type"]]
out=pd.concat([centroids,out_alt],ignore_index=True)
assert out["id"].is_unique
assert out["tpu_id"].nunique()==gdf[idcol].astype(str).nunique()
output=INPUT_DIR/"tpu_alt_origins_v3.csv"
out.to_csv(output, index=False)
print(f"Wrote {len(out)} routing origin points across {out.tpu_id.nunique()} TPUs: "
      f"{len(centroids)} frozen centroids plus {len(out_alt)} unweighted alternatives.")
print(f"Output: {output.relative_to(ROOT)}")
