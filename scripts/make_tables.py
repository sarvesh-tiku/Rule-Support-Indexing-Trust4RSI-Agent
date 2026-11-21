"""Writes the LaTeX tables for the paper from the analysis summary.

Usage:  python3 scripts/make_tables.py results/final_summary.json results/final_diag.json paper
"""
import json
import sys


def ci(r, digits=1):
    return f"${r['diff']:+.{digits}f}$ {{\\footnotesize[{r['lo']:.{digits}f}, {r['hi']:.{digits}f}]}}"


def main():
    summary, diag, outdir = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3]
    sizes = sorted({r["W"] for r in summary["primary"]})
    prim = {(r["W"], r["a"], r["b"], r["metric"]): r for r in summary["primary"]}
    ctrl = {(r["W"], r["condition"], r["a"], r["b"]): r for r in summary["controls"]}

    def row(label, cells):
        return label + " & " + " & ".join(cells) + " \\\\"

    L = ["\\begin{tabular}{@{}lccc@{}}", "\\toprule",
         " & " + " & ".join(f"${w}\\times{w}$" for w in sizes) + " \\\\", "\\midrule",
         "\\multicolumn{4}{@{}l}{\\emph{Relevant violations pooled (block, slow, unlock)}} \\\\",
         row("Episodes", [str(prim[(w, "repair", "replan", "post")]["n"]) for w in sizes]),
         row("Replanning work, indexed $/$ full", [f"{prim[(w, 'repair', 'replan', 'post')]['ratio']:.2f}" for w in sizes]),
         row("Actions, indexed $-$ full", ["0 (identical)" if prim[(w, "repair", "replan", "actions")]["identical"]
                                           else ci(prim[(w, "repair", "replan", "actions")]) for w in sizes]),
         row("Actions, probing $-$ no probing", [ci(prim[(w, "repair_probe", "repair", "actions")]) for w in sizes]),
         row("Actions, probing $-$ posterior sampling", [ci(prim[(w, "repair_probe", "psrl", "actions")]) for w in sizes]),
         row("Actions, probing $-$ generic probing", [ci(prim[(w, "repair_probe", "ig_replan", "actions")]) for w in sizes]),
         row("Probing work, indexed $/$ unindexed", [f"{prim[(w, 'repair_probe', 'replan_probe', 'post')]['ratio']:.2f}" for w in sizes]),
         "\\midrule", "\\multicolumn{4}{@{}l}{\\emph{No violation}} \\\\",
         row("Actions, revising $-$ not revising", [ci(ctrl[(w, "none", "repair", "reactive")]) for w in sizes]),
         row("Actions, probing $-$ no probing", [ci(ctrl[(w, "none", "repair_probe", "repair")]) for w in sizes]),
         "\\midrule", "\\multicolumn{4}{@{}l}{\\emph{True rule outside the hypothesis space}} \\\\",
         row("Actions, probing $-$ no probing", [ci(ctrl[(w, "ool", "repair_probe", "repair")]) for w in sizes]),
         "\\midrule", "\\multicolumn{4}{@{}l}{\\emph{Index against ground truth (all conditions)}} \\\\",
         row("Repairs checked", [f"{diag[str(w)]['repairs']:,}" for w in sizes]),
         row("Repaired plan $\\neq$ fresh plan", [str(diag[str(w)]["mismatch"]) for w in sizes]),
         row("Changed legs missed", [str(diag[str(w)]["missed"]) for w in sizes]),
         row("Legs invalidated", [f"{100 * diag[str(w)]['flagged_fraction']:.0f}\\%" for w in sizes]),
         row("Legs that really changed", [f"{100 * diag[str(w)]['changed_fraction']:.0f}\\%" for w in sizes])]
    if len(sys.argv) > 5:      # post-hoc rows: direct-support-only baseline and wall-clock time
        val, tim = json.load(open(sys.argv[4])), json.load(open(sys.argv[5]))
        v = lambda w: val["by_size"][f"{w}/all"]
        L += ["\\midrule", "\\multicolumn{4}{@{}l}{\\emph{Added after the planned analysis}$^\\dagger$} \\\\",
              row("Direct support only: non-optimal repairs; extra actions, mean (max)",
                  [f"{100 * v(w)['stale_repairs'] / v(w)['repairs']:.1f}\\%; {v(w)['mean_extra_actions']:.2f} ({v(w)['max_extra_actions']})" for w in sizes]),
              row("Time, indexed $/$ full replanning without index",
                  [f"{tim['by_size'][str(w)]['ratio_planning_time_vs_replan_without_index']:.2f}" for w in sizes])]
    if len(sys.argv) > 6:      # leg-table replay against incremental search
        inc = json.load(open(sys.argv[6]))["by_size"]
        frac = lambda w, m: f"{inc[str(w)][m]['expansions'] / inc[str(w)]['astar_all']['expansions'] + 1e-9:.2f}"
        L.append(row("Leg-table search $/$ A* on all legs: index, LPA*, both",
                     [", ".join(frac(w, m) for m in ("astar_index", "lpa_all", "lpa_index")) for w in sizes]))
    L += ["\\bottomrule", "\\end{tabular}"]
    with open(f"{outdir}/table_primary.tex", "w") as f:
        f.write("\n".join(L) + "\n")

    agents = [("reactive", "No rev."), ("repair", "Revise"), ("psrl", "Post.\\ samp."),
              ("ig_replan", "Generic"), ("repair_probe", "Plan-rel.")]
    L = ["\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{@{}l" + "r" * len(agents) + "@{}}", "\\toprule",
         "$\\lambda$ & " + " & ".join(n for _, n in agents) + " \\\\", "\\midrule"]
    for w in sizes:
        L.append(f"\\multicolumn{{{len(agents) + 1}}}{{@{{}}l}}{{\\emph{{${w}\\times{w}$}}}} \\\\")
        for lam in ("0.0", "0.001", "0.01"):
            vals = summary["total_cost"][f"{w}/{lam}"]
            best = min(vals[a] for a, _ in agents)
            L.append(f"{float(lam):g} & " + " & ".join(
                (f"\\textbf{{{vals[a]:.0f}}}" if vals[a] == best else f"{vals[a]:.0f}") for a, _ in agents) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    with open(f"{outdir}/table_total.tex", "w") as f:
        f.write("\n".join(L) + "\n")
    print("wrote tables to", outdir)


if __name__ == "__main__":
    main()
