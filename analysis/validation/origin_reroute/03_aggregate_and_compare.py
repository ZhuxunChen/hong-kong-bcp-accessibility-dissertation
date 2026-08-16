#!/usr/bin/env python3
"""Aggregate the alt-origin runs (>=3 of 5 present, cross-run median), reduce to one value per TPU
(best-case = min across its interior points; and mean-case), then compare to the frozen
centroid baseline. Reads frozen accessibility_tpu_v3.csv; writes only a new comparison CSV/report."""
import json
import pandas as pd, numpy as np
from pathlib import Path
from scipy.stats import spearmanr
ROOT = Path(__file__).resolve().parents[3]
ALT_ROOT = ROOT/"analysis/stage9a/alt_origin_runs"
OUTPUT_DIR = ROOT/"reference_outputs/validation/origin_reroute"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
runs = sorted(ALT_ROOT.glob("run_*/travel_time_matrix_alt_v3.csv"))
if len(runs) != 5:
    runs = sorted((ROOT/"reference_outputs/validation/origin_reroute/runs").glob("run_*_travel_time_matrix_alt_v3.csv"))
assert len(runs) == 5, f"formal comparison requires 5 alt runs, found {len(runs)}"
frames=[pd.read_csv(p)[["from_id","to_id","travel_time_p50"]] for p in runs]
allm=pd.concat(frames)
# 3-of-5 stability + cross-run median per (from_id,to_id)
g=allm.groupby(["from_id","to_id"])["travel_time_p50"]
agg=g.agg(["count","median"]).reset_index()
agg=agg[agg["count"]>=3].rename(columns={"median":"p50"})
# map alt origin id -> tpu_id
alt_input = ALT_ROOT/"inputs/tpu_alt_origins_v3.csv"
if not alt_input.exists():
    alt_input = ROOT/"reference_outputs/validation/origin_reroute/tpu_alt_origins_v3.csv"
alt=pd.read_csv(alt_input)[["id","tpu_id","origin_type"]]
alt["id"]=alt["id"].astype(str); alt["tpu_id"]=alt["tpu_id"].astype(str)
agg=agg.merge(alt,left_on="from_id",right_on="id")
# Per alternative point, take the minimum over six BCPs. Points with no stable
# route within the 120-minute cap must not disappear from the TPU mean; code
# them at the censoring threshold (120), which is conservative for burden.
stable_pt=agg.groupby(["tpu_id","from_id"])["p50"].min().reset_index(name="pt_min_tt")
per_pt=alt.rename(columns={"id":"from_id"}).merge(stable_pt,on=["tpu_id","from_id"],how="left")
per_pt["has_stable_route"]=per_pt["pt_min_tt"].notna()
per_pt["pt_min_tt"]=per_pt["pt_min_tt"].fillna(120.0)
best=per_pt.groupby("tpu_id")["pt_min_tt"].min().reset_index(name="alt_best_min_tt")
alt_only=per_pt[per_pt["origin_type"]!="frozen_centroid"].copy()
alt_only["point_zero_access_60"]=alt_only["pt_min_tt"]>60
mean=alt_only.groupby("tpu_id")["pt_min_tt"].mean().reset_index(name="alt_mean_min_tt_censored120")
rerouted_centroid=(per_pt[per_pt["origin_type"]=="frozen_centroid"]
    [["tpu_id","pt_min_tt"]].rename(columns={"pt_min_tt":"rerouted_centroid_min_tt"}))
coverage=alt_only.groupby("tpu_id").agg(
    alt_points=("from_id","size"),
    alt_points_with_stable_route=("has_stable_route","sum"),
    alt_point_zero_access_share=("point_zero_access_60","mean")
).reset_index()
# frozen centroid baseline
frozen_result = ROOT/"analysis/stage9a/results/accessibility_tpu_v3.csv"
if not frozen_result.exists():
    frozen_result = ROOT/"reference_outputs/stage9a/results/accessibility_tpu_v3.csv"
froz=pd.read_csv(frozen_result)[["area_id","min_tt","bcps_within_60"]]
froz["area_id"]=froz["area_id"].astype(str)
best["tpu_id"]=best["tpu_id"].astype(str); mean["tpu_id"]=mean["tpu_id"].astype(str)
cmp=(froz.merge(best,left_on="area_id",right_on="tpu_id",how="left")
         .merge(mean,on="tpu_id",how="left")
         .merge(rerouted_centroid,on="tpu_id",how="left")
         .merge(coverage,on="tpu_id",how="left"))
n=len(froz)
assert len(cmp)==n and cmp[["alt_best_min_tt","alt_mean_min_tt_censored120","rerouted_centroid_min_tt"]].notna().all().all()
def zero_count(series): return int((series>60).sum())
def zero_share(series): return zero_count(series)/n*100
frozen_zero=int((froz['bcps_within_60']==0).sum())
best_zero=zero_count(cmp['alt_best_min_tt'])
mean_zero=zero_count(cmp['alt_mean_min_tt_censored120'])
mean_case_expected_share=float(cmp['alt_point_zero_access_share'].mean()*100)
rerouted_centroid_zero=zero_count(cmp['rerouted_centroid_min_tt'])
rho_best=float(spearmanr(cmp['min_tt'],cmp['alt_best_min_tt']).correlation)
rho_mean=float(spearmanr(cmp['min_tt'],cmp['alt_mean_min_tt_censored120']).correlation)
rho_centroid=float(spearmanr(cmp['min_tt'],cmp['rerouted_centroid_min_tt']).correlation)
print(f"frozen TPUs={n}")
print(f"frozen zero-access(60) = {frozen_zero}/{n} = {frozen_zero/n*100:.1f}%")
print(f"alt sampled BEST-case zero-access(60) = {best_zero}/{n} = {best_zero/n*100:.1f}%  (optimistic improvement scenario)")
print(f"alt MEAN-case zero-access(60) = {mean_case_expected_share:.1f}%  (TPU-equal mean of sampled point-level zero-access shares)")
print(f"TPUs whose censored mean min_tt exceeds 60 = {mean_zero}/{n} = {mean_zero/n*100:.1f}%  (secondary diagnostic)")
print(f"re-routed frozen centroid zero-access(60) = {rerouted_centroid_zero}/{n} = {rerouted_centroid_zero/n*100:.1f}%")
print(f"mean min_tt: frozen {froz['min_tt'].mean():.1f} | alt-best {cmp['alt_best_min_tt'].mean():.1f} | alt-mean-censored120 {cmp['alt_mean_min_tt_censored120'].mean():.1f}")
print(f"Spearman rank corr (frozen vs alt-best): {rho_best:.3f}")
print(f"Spearman rank corr (frozen vs alt-mean): {rho_mean:.3f}")
print(f"Spearman rank corr (frozen vs re-routed centroid): {rho_centroid:.3f}")
cmp["delta_best"]=cmp["alt_best_min_tt"]-cmp["min_tt"]
cmp["delta_mean"]=cmp["alt_mean_min_tt_censored120"]-cmp["min_tt"]
print("largest improvements (alt-best - frozen):")
print(cmp.nsmallest(5,"delta_best")[["area_id","min_tt","alt_best_min_tt","delta_best"]].to_string(index=False))
print("largest worsenings:")
print(cmp.nlargest(5,"delta_best")[["area_id","min_tt","alt_best_min_tt","delta_best"]].to_string(index=False))
t622=cmp[cmp["area_id"]=="622"]
if len(t622): print("TPU 622:", t622[["min_tt","rerouted_centroid_min_tt","alt_best_min_tt","alt_mean_min_tt_censored120"]].to_dict("records")[0])
comparison_path=OUTPUT_DIR/"origin_reroute_comparison.csv"
cmp.to_csv(comparison_path,index=False)
summary={
    "stable_routed_tpus": n,
    "routing_origin_points": int(len(alt)),
    "unweighted_alternative_origin_points": int(len(alt_only)),
    "alternative_origin_tpus": int(alt["tpu_id"].nunique()),
    "routing_repetitions": len(runs),
    "frozen_zero_access_count": frozen_zero,
    "frozen_zero_access_share_pct": frozen_zero/n*100,
    "alt_sampled_best_zero_access_count": best_zero,
    "alt_sampled_best_zero_access_share_pct": best_zero/n*100,
    "alt_mean_censored120_zero_access_count": mean_zero,
    "alt_mean_censored120_zero_access_share_pct": mean_zero/n*100,
    "alt_mean_case_expected_zero_access_share_pct": mean_case_expected_share,
    "rerouted_centroid_zero_access_count": rerouted_centroid_zero,
    "rerouted_centroid_zero_access_share_pct": rerouted_centroid_zero/n*100,
    "frozen_mean_min_tt": float(froz["min_tt"].mean()),
    "alt_best_mean_min_tt": float(cmp["alt_best_min_tt"].mean()),
    "alt_mean_censored120_mean_min_tt": float(cmp["alt_mean_min_tt_censored120"].mean()),
    "spearman_frozen_vs_alt_best": rho_best,
    "spearman_frozen_vs_alt_mean": rho_mean,
    "spearman_frozen_vs_rerouted_centroid": rho_centroid,
    "unrouted_alt_points": int((~alt_only["has_stable_route"]).sum()),
    "unrouted_rerouted_centroids": int((~per_pt.loc[per_pt["origin_type"]=="frozen_centroid","has_stable_route"]).sum()),
}
summary_path=OUTPUT_DIR/"origin_reroute_summary.json"
summary_path.write_text(json.dumps(summary,indent=2)+"\n")
print(f"\nWrote {comparison_path.relative_to(ROOT)}")
print(f"Wrote {summary_path.relative_to(ROOT)}")
