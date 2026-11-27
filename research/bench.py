"""The benchmark behind the notes (main.tex): each claim a theorem, each checked on Garnet random MDPs over many
seeds, reported as an interquartile mean with a bootstrap 95% interval (Agarwal et al. 2021; Patterson et al. 2024).
numpy only, ~1 min of one core. Writes results.json and data/*.csv (what the figures in the notes plot).

    ~/minish-rl/.venv/bin/python bench.py [--seeds 20]
"""

import argparse
import csv
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

GAMMA = 0.9
HERE = Path(__file__).parent
DATA = HERE / "data"


# ---- statistics ------------------------------------------------------------------------------------------------
def iqm(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    return float(x[n // 4: n - n // 4].mean()) if n >= 4 else float(x.mean())


BOOT = np.random.default_rng(1)


def ci(x, stat=iqm, reps=2000, rng=BOOT):
    """A percentile bootstrap 95% interval of `stat` over runs."""
    x = np.asarray(x, float)
    b = [stat(rng.choice(x, len(x))) for _ in range(reps)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def summary(x):
    return {"iqm": iqm(x), "ci95": ci(x), "min": float(np.min(x)), "max": float(np.max(x)), "runs": len(x)}


def write(name, header, rows):
    DATA.mkdir(exist_ok=True)
    with open(DATA / f"{name}.csv", "w", newline="") as f:
        w = csv.writer(f, delimiter=" ")
        w.writerow(header)
        w.writerows([[f"{v:.6g}" if isinstance(v, float) else v for v in r] for r in rows])


# ---- MDPs ------------------------------------------------------------------------------------------------------
def garnet(rng, S=30, A=4, b=5, K=4):
    """A Garnet MDP G(S, A, b): b next states per (s, a), drawn at random, their probabilities from b-1 uniform cut
    points; reward features phi(s, a) in [0, 1]^K (one per reward kind)."""
    P = np.zeros((S, A, S))
    for s in range(S):
        for a in range(A):
            nxt = rng.choice(S, b, replace=False)
            cuts = np.sort(rng.random(b - 1))
            P[s, a, nxt] = np.diff(np.concatenate([[0], cuts, [1]]))
    return P, rng.random((S, A, K))


def evaluate(P, r, pi, g=GAMMA):
    S = P.shape[0]
    V = np.linalg.solve(np.eye(S) - g * P[np.arange(S), pi], r[np.arange(S), pi])
    return r + g * np.tensordot(P, V, axes=([2], [0]))


def optimal(P, r, g=GAMMA, tol=1e-10):
    Q = np.zeros(r.shape)
    while True:
        Q2 = r + g * P @ Q.max(1)
        if np.abs(Q2 - Q).max() < tol:
            return Q2
        Q = Q2


# ---- E1: successor features ------------------------------------------------------------------------------------
def e1(seeds, steps=300000, every=25000):
    exact, curves = [], []
    for sd in range(seeds):
        rng = np.random.default_rng(sd)
        P, phi = garnet(rng)
        S, A, K = phi.shape
        pi = rng.integers(0, A, S)
        psi = evaluate(P, phi, pi)
        exact.append(max(np.abs(psi @ w - evaluate(P, phi @ w, pi)).max() for w in rng.normal(size=(50, K))))
        est, seen, s, curve = np.zeros_like(psi), np.zeros((S, A)), 0, []
        cum, acts, us = P.cumsum(2), rng.integers(A, size=steps), rng.random(steps)
        for t in range(1, steps + 1):
            a = acts[t - 1]
            s2 = min(int(np.searchsorted(cum[s, a], us[t - 1])), S - 1)
            seen[s, a] += 1
            est[s, a] += (phi[s, a] + GAMMA * est[s2, pi[s2]] - est[s, a]) / seen[s, a] ** 0.7
            s = s2
            if t % every == 0:
                curve.append(np.abs(est - psi).max() / np.abs(psi).max())
        curves.append(curve)
    curves = np.array(curves)
    write("e1_td", ["samples", "iqm", "lo", "hi"],
          [[(i + 1) * every, iqm(c), *ci(c)] for i, c in enumerate(curves.T)])
    return {"exact_max_error": summary(exact), "td_final_relative_error": summary(curves[:, -1])}


# ---- E2: generalised policy improvement ------------------------------------------------------------------------
def e2(seeds, tasks=40):
    margins, slack, gaps, pts = [], [], [], []
    for sd in range(seeds):
        rng = np.random.default_rng(100 + sd)
        P, phi = garnet(rng)
        K = phi.shape[2]
        base = list(np.eye(K))
        psis = [evaluate(P, phi, optimal(P, phi @ w).argmax(1)) for w in base]
        for w in rng.normal(size=(tasks, K)):
            Qs = np.stack([p @ w for p in psis])
            Qg = evaluate(P, phi @ w, Qs.max(0).argmax(1))
            Qstar = optimal(P, phi @ w)
            d = min(np.abs(phi @ (w - wi)).max() for wi in base)
            gap = (Qstar - Qg).max()
            margins.append((Qg - Qs.max(0)).min())
            slack.append(2 * d / (1 - GAMMA) - gap)
            gaps.append(gap / np.abs(Qstar).max())
            pts.append([d, gap, 2 * d / (1 - GAMMA), max(gap, 0.0) / (2 * d / (1 - GAMMA))])
    pts.sort()
    write("e2_gap", ["delta", "gap", "bound", "ratio"], pts)
    return {"min_margin_over_best_skill": float(min(margins)), "min_bound_slack": float(min(slack)),
            "relative_gap_to_optimum": summary(gaps), "tasks": len(gaps)}


# ---- E3: conflict, split, merge --------------------------------------------------------------------------------
PAIRS = {"identical": 1.0, "twice": 2.0, "opposite": -1.0}


def e3(seeds, n=200, d=8, steps=3000):
    exact, steps_to_split, traces = {k: [] for k in PAIRS}, {k: [] for k in PAIRS}, {}
    for sd in range(seeds):
        rng = np.random.default_rng(200 + sd)
        X, u = rng.normal(size=(n, d)), rng.normal(size=d)
        y1 = X @ u
        Pm = X @ np.linalg.pinv(X)
        for k, c in PAIRS.items():
            y2 = c * y1
            th = np.linalg.lstsq(np.vstack([X, X]), np.concatenate([y1, y2]), rcond=None)[0]
            shared = ((X @ th - y1) ** 2).sum() + ((X @ th - y2) ** 2).sum()
            exact[k].append(abs(shared - 0.5 * ((Pm @ (y1 - y2)) ** 2).sum()))
            th, ema, at, tr = np.zeros(d), 0.0, None, []
            for t in range(1, steps + 1):
                i = rng.integers(n, size=16)
                g1, g2 = X[i].T @ (X[i] @ th - y1[i]), X[i].T @ (X[i] @ th - y2[i])
                nrm = np.linalg.norm(g1) * np.linalg.norm(g2)
                ema = 0.98 * ema + 0.02 * (g1 @ g2 / nrm if nrm > 1e-9 else 0.0)
                th -= 0.01 * (g1 + g2) / 16
                if at is None and t > 200 and ema < -0.9:
                    at = t
                if sd == 0 and t % 25 == 0:
                    tr.append(ema)
            steps_to_split[k].append(at if at is not None else np.inf)
            if sd == 0:
                traces[k] = tr
    write("e3_cos", ["step", *PAIRS], [[(i + 1) * 25, *(traces[k][i] for k in PAIRS)] for i in range(len(traces["twice"]))])
    return {k: {"max_error_vs_theory": float(max(exact[k])),
                "split_share": float(np.mean(np.isfinite(steps_to_split[k]))),
                "steps_to_split_iqm": iqm([s for s in steps_to_split[k] if np.isfinite(s)]) if np.isfinite(steps_to_split[k]).any() else None}
            for k in PAIRS}


# ---- E4: reward kinds from gradients ---------------------------------------------------------------------------
def e4(seeds, n=300, d=10, kinds=3, events=9, noise=0.3):
    agree, found, within, across = [], [], [], []
    for sd in range(seeds):
        rng = np.random.default_rng(300 + sd)
        X, dirs = rng.normal(size=(n, d)), rng.normal(size=(kinds, d))
        label = np.arange(events) % kinds
        G = np.stack([-X.T @ (X @ (dirs[k] * rng.uniform(0.5, 3)) + rng.normal(scale=noise, size=n)) for k in label])
        nr = np.linalg.norm(G, axis=1)
        C = G @ G.T / np.outer(nr, nr)
        group, f = -np.ones(events, int), 0
        for e in range(events):
            if group[e] < 0:
                group[(C[e] > 0.9) & (group < 0)] = f
                f += 1
        pairs = lambda g: {(i, j) for i in range(events) for j in range(i + 1, events) if g[i] == g[j]}
        agree.append(len(pairs(group) & pairs(label)) / max(1, len(pairs(group) | pairs(label))))
        found.append(f)
        within += [C[i, j] for i, j in pairs(label)]
        across += [C[i, j] for i in range(events) for j in range(i + 1, events) if label[i] != label[j]]
        if sd == 0:
            write("e4_cos", ["i", "j", "cos"], [[i, j, float(C[i, j])] for i in range(events) for j in range(events)])
    return {"pair_agreement": summary(agree), "kinds_found_share_right": float(np.mean(np.array(found) == kinds)),
            "min_cos_within": float(min(within)), "max_cos_across": float(max(across))}


# ---- E5: what the reward pays decides what is done --------------------------------------------------------------
def reaches(pay_side, pay_goal, dist, side=6, H=16, g=0.97):
    @lru_cache(None)
    def V(c, t):
        opts = [(0.0, False)]
        if t + dist <= H:
            opts.append((g ** (t + dist) * pay_goal, True))
        if c < side and t + 2 <= H:
            v, r = V(c + 1, t + 2)
            opts.append((g ** (t + 1) * pay_side + v, r))
        return max(opts, key=lambda o: (round(o[0], 12), not o[1]))      # (a tie: the goal not counted as sought)
    return V(0, 0)[1]


def e5():
    rows = [[p, dd, int(reaches(p, 1.0, dd))] for p in (0.05, 0.1, 0.2, 0.3, 0.5) for dd in (4, 6, 8, 10, 12)]
    write("e5_sweep", ["pay", "dist", "reached"], rows)
    return {"achievement_only_reaches": reaches(0.3, 0.0, 8), "verified_goal_reaches": reaches(0.0, 1.0, 8),
            "mixed_share_reaching": float(np.mean([r[2] for r in rows]))}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    n = ap.parse_args().seeds
    res = {"seeds": n, "E1": e1(n), "E2": e2(n), "E3": e3(n), "E4": e4(n), "E5": e5()}
    (HERE / "results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
