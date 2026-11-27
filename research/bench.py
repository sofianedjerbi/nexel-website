"""The simulations behind the research notes (notes/main.tex), revision 3. numpy only, under a minute on one core.
Writes results.json and data/*.csv (what the notes' figures plot).

    python bench.py [--seeds 20]

E1  successor features: Q^pi_w = psi^pi . w, an identity, checked once (Garnet MDPs)
E2  GPI on Garnet MDPs: how good the combined policy is, from a random policy (0) to the optimum (1), against the
    best single skill; and how often the theorem's bound says more than the trivial one
S   potential-based shaping on a small build task: the optimal policy unchanged (checked exactly), and how many
    episodes Q-learning needs with the sparse reward and with the shaped one, over seeds
B   the executor's simulator board (data/sim_board.csv): the share of designs standing, with a Wilson interval
"""

import argparse
import csv
import json
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
def e1(seeds):
    """The identity, once per Garnet: the value of a fixed policy under any weighting, from features learned once."""
    worst = 0.0
    for sd in range(seeds):
        rng = np.random.default_rng(sd)
        P, phi = garnet(rng)
        pi = rng.integers(0, phi.shape[1], phi.shape[0])
        psi = evaluate(P, phi, pi)
        worst = max(worst, max(np.abs(psi @ w - evaluate(P, phi @ w, pi)).max() for w in rng.normal(size=(50, phi.shape[2]))))
    return {"max_abs_error": float(worst)}


# ---- E2: generalised policy improvement ------------------------------------------------------------------------
def evaluate_random(P, r, g=GAMMA):
    S = r.shape[0]
    V = np.linalg.solve(np.eye(S) - g * P.mean(1), r.mean(1))
    return V


def e2(seeds, tasks=40):
    """Per new task w: the mean over states of V, normalised so a uniform random policy is 0 and the optimum 1, for
    the GPI policy and for the best single base skill; and whether the bound 2 delta/(1-gamma) beats the trivial
    (r_max - r_min)/(1-gamma)."""
    rows, vacuous = [], 0
    for sd in range(seeds):
        rng = np.random.default_rng(100 + sd)
        P, phi = garnet(rng)
        K = phi.shape[2]
        base = list(np.eye(K))
        pols = [optimal(P, phi @ w).argmax(1) for w in base]
        psis = [evaluate(P, phi, p) for p in pols]
        for w in rng.normal(size=(tasks, K)):
            r = phi @ w
            gpi = np.stack([p @ w for p in psis]).max(0).argmax(1)
            def v(pi, P=P, r=r):
                return evaluate(P, r, pi)[np.arange(len(pi)), pi].mean()
            vstar, vrand = optimal(P, r).max(1).mean(), evaluate_random(P, r).mean()
            span = vstar - vrand
            if span < 1e-9:
                continue
            g = (v(gpi) - vrand) / span
            best = max((v(p) - vrand) / span for p in pols)
            rows.append([best, g])
            d = min(np.abs(phi @ (w - wi)).max() for wi in base)
            vacuous += 2 * d >= r.max() - r.min()
    rows = np.array(rows)
    write("e2_norm", ["best_skill", "gpi"], rows.tolist())
    return {"gpi_normalised": summary(rows[:, 1]), "gpi_minus_best_skill": summary(rows[:, 1] - rows[:, 0]),
            "share_gpi_above_best_skill": float(np.mean(rows[:, 1] > rows[:, 0] + 1e-9)),
            "share_bound_vacuous": float(vacuous / len(rows)), "tasks": len(rows)}


# ---- S: potential-based shaping on a build task ------------------------------------------------------------------
L_, N_, H_, G_ = 8, 4, 100, 0.97      # positions, site cells at the far end, steps an episode, discount
SITE_ = list(range(L_ - N_, L_))


def build_mdp():
    """A line of L positions: blocks taken at 0, a site of N cells at the far end. State (pos, carrying, filled mask).
    Actions: left, right, take (at 0), place (on an empty site cell, carrying), dig (a filled site cell: the block
    back in hand if the hand is free). Reward 1 when the last cell is filled; the episode ends."""
    S = L_ * 2 * 2 ** N_
    nxt, rew, done = np.zeros((S, 5), int), np.zeros((S, 5)), np.zeros((S, 5), bool)
    def idx(p, c, m):
        return (p * 2 + c) * 2 ** N_ + m
    for p in range(L_):
        for c in (0, 1):
            for m in range(2 ** N_):
                s = idx(p, c, m)
                k = p - SITE_[0]
                for a in range(5):
                    p2, c2, m2 = p, c, m
                    if a == 0:
                        p2 = max(0, p - 1)
                    elif a == 1:
                        p2 = min(L_ - 1, p + 1)
                    elif a == 2 and p == 0:
                        c2 = 1
                    elif a == 3 and k >= 0 and c and not m >> k & 1:
                        c2, m2 = 0, m | 1 << k
                    elif a == 4 and k >= 0 and m >> k & 1:
                        c2, m2 = 1, m & ~(1 << k)                # (the hand ends full: a block held is dropped)
                    nxt[s, a] = idx(p2, c2, m2)
                    if m2 == 2 ** N_ - 1 and m != m2:
                        rew[s, a], done[s, a] = 1.0, True
    phi = np.array([bin(s % 2 ** N_).count("1") / N_ for s in range(S)])
    return nxt, rew, done, phi, idx(0, 0, 0)


def shaped(rew, done, nxt, phi):
    """F = gamma Phi(s') - Phi(s), Phi(terminal) = 0 (Ng, Harada, Russell 1999)."""
    return rew + np.where(done, 0.0, G_ * phi[nxt]) - phi[:, None]


def solve(nxt, r, done):
    Q = np.zeros(r.shape)
    for _ in range(3000):
        Q = r + G_ * np.where(done, 0.0, Q.max(1)[nxt])
    return Q


def learn(nxt, r, done, start, rng, eps=0.1, alpha=0.5, most=3000):
    """Q-learning, epsilon-greedy from Q = 0; episodes until the greedy policy builds the site within H steps."""
    Q = np.zeros(r.shape)
    for ep in range(1, most + 1):
        s = start
        for _ in range(H_):
            a = rng.integers(5) if rng.random() < eps else int(rng.choice(np.flatnonzero(Q[s] == Q[s].max())))
            t = r[s, a] + (0.0 if done[s, a] else G_ * Q[nxt[s, a]].max())
            Q[s, a] += alpha * (t - Q[s, a])
            if done[s, a]:
                break
            s = nxt[s, a]
        if ep % 10 == 0:
            s = start
            for _ in range(H_):
                a = int(Q[s].argmax())
                if done[s, a]:
                    return ep
                s = nxt[s, a]
    return most


def shaping(seeds):
    nxt, rew, done, phi, start = build_mdp()
    rs = shaped(rew, done, nxt, phi)
    q0, q1 = solve(nxt, rew, done), solve(nxt, rs, done)
    same = bool(np.allclose(q1, q0 - phi[:, None], atol=1e-6))                  # (Q' = Q - Phi: the same argmax)
    dig = [(s, 4) for s in range(len(phi)) if nxt[s, 4] != s and phi[nxt[s, 4]] < phi[s]]
    sparse, shp = [], []
    for sd in range(seeds):
        sparse.append(learn(nxt, rew, done, start, np.random.default_rng(400 + sd)))
        shp.append(learn(nxt, rs, done, start, np.random.default_rng(400 + sd)))
    write("s_episodes", ["seed", "sparse", "shaped"], [[i, a, b] for i, (a, b) in enumerate(zip(sparse, shp, strict=True))])
    return {"optimal_policy_unchanged": same, "every_dig_of_a_standing_cell_pays_below_zero": bool(all(rs[s, a] < 0 for s, a in dig)),
            "episodes_sparse": summary(sparse), "episodes_shaped": summary(shp),
            "paired_ratio_sparse_over_shaped": summary(np.array(sparse) / np.array(shp))}


# ---- B: the simulator board -------------------------------------------------------------------------------------
def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(c - h), float(c + h)]


def board():
    with open(DATA / "sim_board.csv") as f:
        rows = list(csv.DictReader(f, delimiter=" "))
    k, n = sum(int(r["whole"]) for r in rows), len(rows)
    return {"whole": k, "of": n, "share": k / n, "wilson95": wilson(k, n),
            "not_whole": [f"{r['design']} seed {r['seed']}" for r in rows if r["whole"] == "0"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    n = ap.parse_args().seeds
    res = {"seeds": n, "E1": e1(n), "E2": e2(n), "S": shaping(n), "B": board()}
    (HERE / "results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
