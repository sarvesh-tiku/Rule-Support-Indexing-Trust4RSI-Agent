"""RuleGrid: a grid world whose layout is known but whose obstacle rules are uncertain.

Cells are open, wall, or an obstacle of one of K types. Entering an obstacle cell of
type k succeeds with probability p_k; a failed attempt costs one action and leaves the
agent where it was. The agent must step on every shrine (any order) and then the tower.
"""
import random
from collections import deque

OPEN, WALL = -1, -2
VALUES = (0.9, 0.3, 0.0)            # rule values: free, slow, blocked
NOMINAL = (0.9, 0.9, 0.3, 0.0, 0.0)  # believed value for each of the K = 5 types
K = len(NOMINAL)
N_SHRINES = 5
MASK = (1 << 64) - 1


def _mix(z):
    z = (z + 0x9E3779B97F4A7C15) & MASK
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


def hash01(seed, cell, n):
    """Deterministic uniform in [0,1) for the n-th attempt at a cell (common random numbers)."""
    return _mix(_mix(_mix(seed) ^ (cell * 0x100000001B3)) ^ n) / float(1 << 64)


class World:
    def __init__(self, W, grid, start, shrines, tower, seed):
        self.W, self.grid, self.start, self.shrines, self.tower = W, grid, start, shrines, tower
        self.seed = seed
        self.type_cells = [[i for i, t in enumerate(grid) if t == k] for k in range(K)]
        self.p_true = list(NOMINAL)
        self.ool = None          # (type, boundary_x): blocked where x < boundary, free elsewhere
        self.counts = {}

    def clone(self):
        w = World(self.W, self.grid, self.start, self.shrines, self.tower, self.seed)
        w.p_true, w.ool = list(self.p_true), self.ool
        return w

    def true_p(self, cell):
        k = self.grid[cell]
        if self.ool is not None and k == self.ool[0]:
            return 0.0 if cell % self.W < self.ool[1] else 0.9
        return self.p_true[k]

    def attempt(self, cell):
        n = self.counts.get(cell, 0)
        self.counts[cell] = n + 1
        return hash01(self.seed, cell, n) < self.true_p(cell)


def _segment(rng, W, length):
    horizontal = rng.random() < 0.5
    a, b = rng.randrange(W), rng.randrange(max(1, W - length))
    return [(b + i, a) if horizontal else (a, b + i) for i in range(length)]


def _open_connected(W, grid, points):
    seen, queue = {points[0]}, deque([points[0]])
    while queue:
        u = queue.popleft()
        x, y = u % W, u // W
        for vx, vy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= vx < W and 0 <= vy < W:
                v = vy * W + vx
                if v not in seen and grid[v] == OPEN:
                    seen.add(v)
                    queue.append(v)
    return all(p in seen for p in points)


def gen_map(W, seed):
    """Random map. Waypoints are always mutually reachable through open cells alone, so
    every obstacle is a shortcut and never a necessity: any agent can always finish."""
    rng = random.Random(seed * 7919 + W)
    for _ in range(2000):
        grid = [OPEN] * (W * W)
        for _ in range(max(2, W // 3)):
            for x, y in _segment(rng, W, rng.randint(max(2, W // 4), max(3, W // 3))):
                grid[y * W + x] = WALL
        for k in range(K):
            for _ in range(max(2, W // 6)):
                for x, y in _segment(rng, W, rng.randint(max(3, W // 3), max(4, W // 2))):
                    grid[y * W + x] = k
        pts, tries = [], 0
        while len(pts) < N_SHRINES + 2 and tries < 4000:
            tries += 1
            c = rng.randrange(W * W)
            if grid[c] != OPEN:
                continue
            if all(abs(c % W - p % W) + abs(c // W - p // W) >= max(3, W // 4) for p in pts):
                pts.append(c)
        if len(pts) < N_SHRINES + 2 or not _open_connected(W, grid, pts):
            continue
        return World(W, grid, pts[0], pts[1:1 + N_SHRINES], pts[-1], seed)
    raise RuntimeError("could not generate a map")
