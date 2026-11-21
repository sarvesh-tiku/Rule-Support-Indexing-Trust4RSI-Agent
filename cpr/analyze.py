"""Statistics, tables and figures from a results file.

Usage:  python3 -m cpr.analyze results/final.jsonl --out results/final
"""
import argparse
import json
import os

import numpy as np
from scipy.stats import wilcoxon

AGENTS = ["reactive", "replan", "psrl", "ig_replan", "repair", "repair_probe", "replan_probe"]
LABEL = {"oracle": "Oracle", "reactive": "No revision", "replan": "Revise + replan", "psrl": "Posterior sampling",
         "ig_replan": "Generic probing", "repair": "Indexed repair", "repair_probe": "Indexed repair + probing",
         "replan_probe": "Replan + probing"}
CONDS = ["none", "block", "slow", "unlock", "irrelevant", "ool"]
VIOLATIONS = ["block", "slow", "unlock"]          # the primary family: relevant, representable
LAMBDAS = [0.0, 0.001, 0.01]
# Primary comparisons, fixed before the final run: (name, agent A, agent B, metric). Negative = A lower.
PRIMARY = [("P1 compute: indexed repair vs replan", "repair", "replan", "post"),
           ("P1 actions: indexed repair vs replan", "repair", "replan", "actions"),
           ("P2 actions: probing vs no probing", "repair_probe", "repair", "actions"),
           ("P3 actions: probing vs posterior sampling", "repair_probe", "psrl", "actions"),
           ("P4 actions: plan-relevant vs generic probing", "repair_probe", "ig_replan", "actions"),
           ("P5 compute: indexed vs unindexed probing", "repair_probe", "replan_probe", "post"),
           ("P5 actions: indexed vs unindexed probing", "repair_probe", "replan_probe", "actions")]


def load(path):
    header, rows = None, []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r.get("header"):
                header = r
            else:
                rows.append(r)
    return header, rows


def boot_ci(x, n_boot=10000, seed=0):
    x = np.asarray(x, float)
    if len(x) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(pvals):
    order = np.argsort(pvals)
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvals) - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()
    header, rows = load(args.results)
    skipped = [r for r in rows if r.get("skipped")]
    rows = [r for r in rows if not r.get("skipped")]
    sizes = sorted({r["W"] for r in rows})
    ep = {}
    for r in rows:
        r["post"] = r["expansions"] - r["exp_initial"]
        ep.setdefault((r["W"], r["condition"], r["seed"]), {})[r["agent"]] = r

    def episodes(W, conds):
        return [v for (w, c, s), v in sorted(ep.items()) if w == W and c in conds]

    out = dict(source_sha256=header["source_sha256"], params=header["params"], seeds=header["seeds"],
               n_skipped={}, cells={}, primary=[], controls=[], total_cost={}, reuse={})
    for r in skipped:
        key = f"{r['W']}/{r['condition']}"
        out["n_skipped"][key] = out["n_skipped"].get(key, 0) + 1

    # ---- descriptive cells
    for W in sizes:
        for c in CONDS:
            eps = episodes(W, [c])
            if not eps:
                continue
            cell = dict(n=len(eps), oracle_actions=float(np.mean([e["oracle"]["actions"] for e in eps])), agents={})
            for a in AGENTS:
                if a not in eps[0]:
                    continue
                reg = [e[a]["actions"] - e["oracle"]["actions"] for e in eps]
                lo, hi = boot_ci(reg)
                cell["agents"][a] = dict(
                    regret=float(np.mean(reg)), regret_lo=lo, regret_hi=hi,
                    actions=float(np.mean([e[a]["actions"] for e in eps])),
                    expansions=float(np.mean([e[a]["expansions"] for e in eps])),
                    post=float(np.mean([e[a]["post"] for e in eps])),
                    probes=float(np.mean([e[a]["probes"] for e in eps])),
                    triggers=float(np.mean([e[a]["triggers"] for e in eps])),
                    completed=float(np.mean([e[a]["completed"] for e in eps])))
            out["cells"][f"{W}/{c}"] = cell

    # ---- primary comparisons, pooled over the three relevant violation types
    pvals = []
    for W in sizes:
        eps = episodes(W, VIOLATIONS)
        for name, a, b, metric in PRIMARY:
            d = np.array([e[a][metric] - e[b][metric] for e in eps], float)
            lo, hi = boot_ci(d)
            p = 1.0 if np.all(d == 0) else float(wilcoxon(d, zero_method="wilcox").pvalue)
            mb = float(np.mean([e[b][metric] for e in eps]))
            out["primary"].append(dict(W=W, name=name, a=a, b=b, metric=metric, n=len(d), mean_a=float(np.mean(
                [e[a][metric] for e in eps])), mean_b=mb, diff=float(d.mean()), lo=lo, hi=hi,
                ratio=float(np.mean([e[a][metric] for e in eps]) / mb) if mb else float("nan"),
                identical=bool(np.all(d == 0)), p=p))
            pvals.append(p)
    for row, padj in zip(out["primary"], holm(pvals)):
        row["p_holm"] = padj

    # ---- controls and the out-of-language condition: probing agent vs indexed repair, and vs no revision
    for W in sizes:
        for c in ("none", "irrelevant", "ool"):
            eps = episodes(W, [c])
            if len(eps) < 2:
                continue
            for a, b in (("repair_probe", "repair"), ("repair", "reactive"), ("repair", "psrl")):
                d = np.array([e[a]["actions"] - e[b]["actions"] for e in eps], float)
                lo, hi = boot_ci(d)
                out["controls"].append(dict(W=W, condition=c, a=a, b=b, n=len(d), diff=float(d.mean()), lo=lo, hi=hi,
                                            oracle=float(np.mean([e["oracle"]["actions"] for e in eps]))))

    # ---- total cost = actions + lambda * expansions, as regret against the oracle's actions
    for W in sizes:
        eps = episodes(W, VIOLATIONS)
        for lam in LAMBDAS:
            out["total_cost"][f"{W}/{lam}"] = {
                a: float(np.mean([e[a]["actions"] + lam * e[a]["expansions"] - e["oracle"]["actions"] for e in eps]))
                for a in AGENTS if a in eps[0]}

    # ---- how much of the leg table the index kept
    for W in sizes:
        eps = episodes(W, VIOLATIONS)
        rec = sum(e["repair"]["legs_recomputed"] for e in eps)
        reu = sum(e["repair"]["legs_reused"] for e in eps)
        out["reuse"][str(W)] = dict(reused_fraction=reu / max(1, reu + rec - 15 * len(eps)),
                                    noops=float(np.mean([e["repair"]["noops"] for e in eps])),
                                    repairs=float(np.mean([e["repair"]["repairs"] for e in eps])))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out + "_summary.json", "w") as f:
        json.dump(out, f, indent=1)

    # ---- markdown report
    L = [f"# Results: {os.path.basename(args.results)}", "",
         f"Source hash `{header['source_sha256'][:16]}`, map seeds {header['seeds'][0]}–{header['seeds'][1] - 1}, "
         f"parameters {json.dumps(header['params'])}.", "",
         "Regret is actions minus the oracle's actions on the same map and random stream. "
         "Brackets are 95% paired-bootstrap intervals.", ""]
    for W in sizes:
        L += [f"## Board {W}×{W}", "", "| Condition | n | " + " | ".join(LABEL[a] for a in AGENTS) + " |",
              "|---|---|" + "---|" * len(AGENTS)]
        for c in CONDS:
            cell = out["cells"].get(f"{W}/{c}")
            if cell:
                L.append(f"| {c} | {cell['n']} | " + " | ".join(
                    f"{cell['agents'][a]['regret']:.1f} [{cell['agents'][a]['regret_lo']:.1f}, {cell['agents'][a]['regret_hi']:.1f}]"
                    for a in AGENTS) + " |")
        L += ["", "Planning node expansions after the initial plan (mean):", "",
              "| Condition | " + " | ".join(LABEL[a] for a in AGENTS) + " |", "|---|" + "---|" * len(AGENTS)]
        for c in CONDS:
            cell = out["cells"].get(f"{W}/{c}")
            if cell:
                L.append(f"| {c} | " + " | ".join(f"{cell['agents'][a]['post']:.0f}" for a in AGENTS) + " |")
        L.append("")
    L += ["## Primary comparisons (block, slow and unlock pooled)", "",
          "| Board | Comparison | n | A | B | A − B [95% CI] | A/B | Holm p |", "|---|---|---|---|---|---|---|---|"]
    for r in out["primary"]:
        note = "identical in every episode" if r["identical"] else f"{r['p_holm']:.2g}"
        L.append(f"| {r['W']} | {r['name']} | {r['n']} | {r['mean_a']:.1f} | {r['mean_b']:.1f} | "
                 f"{r['diff']:.1f} [{r['lo']:.1f}, {r['hi']:.1f}] | {r['ratio']:.2f} | {note} |")
    L += ["", "## Controls and out-of-language condition (difference in actions, A − B)", "",
          "| Board | Condition | A | B | n | A − B [95% CI] | Oracle actions |", "|---|---|---|---|---|---|---|"]
    for r in out["controls"]:
        L.append(f"| {r['W']} | {r['condition']} | {LABEL[r['a']]} | {LABEL[r['b']]} | {r['n']} | "
                 f"{r['diff']:.1f} [{r['lo']:.1f}, {r['hi']:.1f}] | {r['oracle']:.1f} |")
    L += ["", "## Total-cost regret, actions + λ × expansions (violations pooled)", "",
          "| Board | λ | " + " | ".join(LABEL[a] for a in AGENTS) + " |", "|---|---|" + "---|" * len(AGENTS)]
    for key, vals in out["total_cost"].items():
        W, lam = key.split("/")
        L.append(f"| {W} | {lam} | " + " | ".join(f"{vals[a]:.1f}" for a in AGENTS) + " |")
    L += ["", "## Skipped episodes (no rule on the map fits the condition)", "",
          ", ".join(f"{k}: {v}" for k, v in sorted(out["n_skipped"].items())) or "none", ""]
    with open(args.out + "_report.md", "w") as f:
        f.write("\n".join(L))
    print("\n".join(L))
    if not args.no_figures:
        figures(out, sizes, args.out)


def figures(out, sizes, prefix):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, muted, grid = "#1a1a19", "#5f5e58", "#e4e3dd"
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": grid, "axes.labelcolor": ink, "xtick.color": muted,
                         "ytick.color": muted, "text.color": ink, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    # Figure 1: regret by condition on the middle board. Repair and replan act identically, so one bar.
    W = sizes[len(sizes) // 2]
    shown = [("reactive", "#2a78d6"), ("repair", "#eb6834"), ("psrl", "#1baf7a"), ("ig_replan", "#eda100"),
             ("repair_probe", "#e87ba4")]
    names = {"reactive": "No revision", "repair": "Revise (replan or indexed repair)", "psrl": "Posterior sampling",
             "ig_replan": "Generic probing", "repair_probe": "Plan-relevant probing"}
    conds = [c for c in ["none", "block", "slow", "unlock", "ool"] if f"{W}/{c}" in out["cells"]]
    fig, ax = plt.subplots(figsize=(6.9, 2.5))
    bw = 0.16
    for i, (a, col) in enumerate(shown):
        vals = [out["cells"][f"{W}/{c}"]["agents"][a] for c in conds]
        x = np.arange(len(conds)) + (i - 2) * bw
        y = [v["regret"] for v in vals]
        ax.bar(x, y, bw * 0.86, color=col, label=names[a], linewidth=0)
        ax.errorbar(x, y, yerr=[[v["regret"] - v["regret_lo"] for v in vals], [v["regret_hi"] - v["regret"] for v in vals]],
                    fmt="none", ecolor=ink, elinewidth=0.6, capsize=0)
    ax.set_xticks(np.arange(len(conds)))
    ax.set_xticklabels({"none": "No violation", "block": "Free→blocked", "slow": "Free→slow", "unlock": "Blocked→free",
                        "ool": "Outside hypothesis space"}[c] for c in conds)
    ax.set_ylabel("Regret (actions)")
    ax.yaxis.grid(True, color=grid, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.axhline(0, color=muted, linewidth=0.6)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.32), fontsize=7.5, handlelength=1.2)
    fig.tight_layout()
    fig.savefig(prefix + "_fig_regret.pdf")
    fig.savefig(prefix + "_fig_regret.png", dpi=200)
    plt.close(fig)
    # Figure 2: replanning work with and without the index, by board size.
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.2))
    for ax, (a, b, title) in zip(axes, [("replan", "repair", "No probing"), ("replan_probe", "repair_probe", "With probing")]):
        rows = {r["W"]: r for r in out["primary"] if r["metric"] == "post" and r["a"] == b and r["b"] == a}
        x = np.arange(len(sizes))
        ya, yb = [rows[w]["mean_b"] / 1000 for w in sizes], [rows[w]["mean_a"] / 1000 for w in sizes]
        ax.bar(x - 0.2, ya, 0.36, color="#2a78d6", label="Full replanning", linewidth=0)
        ax.bar(x + 0.2, yb, 0.36, color="#eb6834", label="Support-indexed", linewidth=0)
        for xi, u, v in zip(x, ya, yb):
            ax.text(xi + 0.2, v, f"{v / u:.2f}×", ha="center", va="bottom", fontsize=7, color=ink)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{w}×{w}" for w in sizes])
        ax.set_title(title, fontsize=8, loc="left")
        ax.set_ylabel("Node expansions after\ninitial plan (thousands)")
        ax.yaxis.grid(True, color=grid, linewidth=0.6)
        ax.set_axisbelow(True)
    axes[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(prefix + "_fig_compute.pdf")
    fig.savefig(prefix + "_fig_compute.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
