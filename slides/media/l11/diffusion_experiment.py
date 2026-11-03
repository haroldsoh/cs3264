"""Lecture 11: the diffusion models whose outputs the deck shows.

Two models, both trained with the simple noise-prediction loss of DDPM (Ho, Jain and Abbeel 2020, Algorithm 1)
    J(theta) = E_{x0, t, eps} || eps - eps_theta(x_t, t) ||^2,   x_t = a_t x0 + b_t eps,
    a_t = sqrt(abar_t), b_t = sqrt(1 - abar_t), abar_t = prod_{s <= t} alpha_s, alpha_t = 1 - beta_t,
and sampled with DDPM ancestral sampling (Algorithm 2): sigma_t^2 = beta_t, no noise added at the last step.

  digits : MNIST, pixels scaled to [-1, 1]; T = 1000, beta linear from 1e-4 to 0.02 (DDPM's schedule);
           a small U-Net (32 channels, two resolutions below 28 x 28) with a sinusoidal embedding of t; Adam 2e-4,
           batch 128, an exponential moving average of the weights (0.9995) for sampling.
  two-d  : two Gaussian modes in the plane; T = 100, beta linear from 1e-3 to 0.15; an MLP with an embedding of t.

Images are stored for the deck as 4-bit grey levels of clip((v + 1) / 2, 0, 1), two pixels per byte, base64.
Labels are not used. Pixel values outside [-1, 1] are clipped for display only.

Usage:  python3 diffusion_experiment.py pilot   # 300 updates, timing only
        python3 diffusion_experiment.py         # writes diffusion.json (deck data) and run.log
"""
import base64, json, math, struct, sys, time
from pathlib import Path
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

HERE = Path(__file__).resolve().parent
RAW = Path("/Users/hsoh/Library/CloudStorage/OneDrive-NationalUniversityofSingapore/CS5340/CS5340-notebooks/L9/data/MNIST/raw")
DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = 0

T = 1000
BETA = torch.linspace(1e-4, 0.02, T, dtype=torch.float64)          # beta_1 .. beta_T
ALPHA = 1 - BETA
ABAR = torch.cumprod(ALPHA, 0)
STEPS = 20000                                                       # 60 ms per update on the M3 Pro's GPU (pilot)
BATCH = 128
LR = 2e-4
EMA = 0.9995
N_GEN = 24                                                          # generated digits stored with their chains
FRAMES = [1000, 900, 800, 700, 600, 500, 450, 400, 350, 300, 250, 200, 170, 140, 110, 80, 60, 40, 20, 10, 0]
PRED_T = [900, 700, 500, 300, 100]                                  # noise levels for the clean-image predictions

T2 = 100
BETA2 = torch.linspace(1e-3, 0.15, T2, dtype=torch.float64)
ABAR2 = torch.cumprod(1 - BETA2, 0)
MODES = [(-1.1, 0.7), (1.1, -0.7)]
MODE_SD = 0.22


def idx_images(name):
    b = (RAW / name).read_bytes()
    _, n, h, w = struct.unpack(">IIII", b[:16])
    return np.frombuffer(b, np.uint8, offset=16).reshape(n, h * w).astype(np.float32) / 255.0


def pack4(imgs):
    """images in [-1, 1] (any shape ending in 784) -> base64 of 4-bit grey levels, two pixels per byte"""
    v = np.clip((np.asarray(imgs, np.float64).reshape(-1) + 1) / 2, 0, 1)
    q = np.rint(v * 15).astype(np.uint8)
    if q.size % 2: q = np.append(q, 0)
    return base64.b64encode((q[0::2] << 4 | q[1::2]).astype(np.uint8).tobytes()).decode()


def temb(t, dim):
    """sinusoidal embedding of the level t (an integer tensor)"""
    half = dim // 2
    f = torch.exp(-math.log(10000) * torch.arange(half, device=t.device) / half)
    a = t.float()[:, None] * f[None]
    return torch.cat([a.sin(), a.cos()], 1)


class Res(nn.Module):
    def __init__(self, cin, cout, tdim):
        super().__init__()
        self.n1, self.c1 = nn.GroupNorm(8, cin), nn.Conv2d(cin, cout, 3, padding=1)
        self.t = nn.Linear(tdim, cout)
        self.n2, self.c2 = nn.GroupNorm(8, cout), nn.Conv2d(cout, cout, 3, padding=1)
        self.skip = nn.Conv2d(cin, cout, 1) if cin != cout else nn.Identity()

    def forward(self, x, e):
        h = self.c1(F.silu(self.n1(x))) + self.t(e)[:, :, None, None]
        h = self.c2(F.silu(self.n2(h)))
        return h + self.skip(x)


class UNet(nn.Module):
    """a small U-Net: 28 x 28 -> 14 -> 7 and back, with skip connections; one network for every level t"""
    def __init__(self, c=32, tdim=256):
        super().__init__()
        self.te = nn.Sequential(nn.Linear(128, tdim), nn.SiLU(), nn.Linear(tdim, tdim))
        self.inp = nn.Conv2d(1, c, 3, padding=1)
        self.r1 = Res(c, c, tdim); self.d1 = nn.Conv2d(c, c, 3, 2, 1)
        self.r2 = Res(c, 2 * c, tdim); self.d2 = nn.Conv2d(2 * c, 2 * c, 3, 2, 1)
        self.m1 = Res(2 * c, 2 * c, tdim); self.m2 = Res(2 * c, 2 * c, tdim)
        self.u2 = Res(4 * c, 2 * c, tdim); self.u1 = Res(3 * c, c, tdim)
        self.out = nn.Sequential(nn.GroupNorm(8, c), nn.SiLU(), nn.Conv2d(c, 1, 3, padding=1))

    def forward(self, x, t):
        e = self.te(temb(t, 128))
        x = x.view(-1, 1, 28, 28)
        h1 = self.r1(self.inp(x), e)
        h2 = self.r2(self.d1(h1), e)
        m = self.m2(self.m1(self.d2(h2), e), e)
        u = self.u2(torch.cat([F.interpolate(m, scale_factor=2, mode="nearest"), h2], 1), e)
        u = self.u1(torch.cat([F.interpolate(u, scale_factor=2, mode="nearest"), h1], 1), e)
        return self.out(u).view(-1, 784)


class MLP(nn.Module):
    def __init__(self, h=128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(2 + 32, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(), nn.Linear(h, 2))

    def forward(self, x, t):
        return self.net(torch.cat([x, temb(t, 32)], 1))


def coeffs(abar, t):
    """a_t and b_t for integer levels t (1-based), as float32 columns"""
    ab = abar[t - 1].float()
    return ab.sqrt()[:, None], (1 - ab).sqrt()[:, None]


@torch.no_grad()
def ancestral(net, xT, beta, keep=(), pred_for=None):
    """DDPM Algorithm 2 from x_T; returns {t: x_t} for t in keep and {t: xhat_0} for one chain (index pred_for)"""
    beta = torch.as_tensor(beta, dtype=torch.float64).cpu()
    alpha, abar = 1 - beta, torch.cumprod(1 - beta, 0)
    Tn, x = len(beta), xT.clone()
    xs, preds = {}, {}
    if Tn in keep: xs[Tn] = x.cpu().numpy().copy()
    for t in range(Tn, 0, -1):
        tt = torch.full((len(x),), t, device=x.device, dtype=torch.long)
        eps = net(x, tt)
        a, b = math.sqrt(float(abar[t - 1])), math.sqrt(float(1 - abar[t - 1]))
        if pred_for is not None and t in keep: preds[t] = ((x - b * eps) / a)[pred_for].cpu().numpy().copy()
        mean = (x - float(beta[t - 1]) / b * eps) / math.sqrt(float(alpha[t - 1]))
        x = mean + (math.sqrt(float(beta[t - 1])) * torch.randn_like(x) if t > 1 else 0)
        if t - 1 in keep: xs[t - 1] = x.cpu().numpy().copy()
    if pred_for is not None and 0 in keep: preds[0] = xs[0][pred_for]
    return xs, preds


def train_digits(log, steps):
    torch.manual_seed(SEED); np.random.seed(SEED)
    train = torch.tensor(idx_images("train-images-idx3-ubyte") * 2 - 1)
    test = torch.tensor(idx_images("t10k-images-idx3-ubyte") * 2 - 1)
    net = UNet().to(DEV)
    ema = UNet().to(DEV); ema.load_state_dict(net.state_dict())
    for p in ema.parameters(): p.requires_grad_(False)
    opt = torch.optim.Adam(net.parameters(), LR)
    nparam = sum(p.numel() for p in net.parameters())
    log(f"digits: U-Net with {nparam:,} parameters on {DEV}; {steps} updates, batch {BATCH}")
    g = torch.Generator().manual_seed(SEED)
    t0, run = time.time(), 0.0
    for k in range(1, steps + 1):
        idx = torch.randint(0, len(train), (BATCH,), generator=g)
        x0 = train[idx].to(DEV)
        t = torch.randint(1, T + 1, (BATCH,), device=DEV)
        a, b = coeffs(ABAR.float().to(DEV), t)
        eps = torch.randn_like(x0)
        loss = F.mse_loss(net(a * x0 + b * eps, t), eps)
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        with torch.no_grad():
            pe, pn = list(ema.parameters()), list(net.parameters())
            torch._foreach_mul_(pe, EMA); torch._foreach_add_(pe, pn, alpha=1 - EMA)
        run += loss.detach()
        if k % 1000 == 0 or k == steps:
            n = 1000 if k % 1000 == 0 else k % 1000
            log(f"  update {k:6d}  mean loss {run.item() / n:.4f}  ({time.time() - t0:.0f} s)")
            run = 0.0
    ema.eval()
    # held-out noise-prediction loss of the averaged weights, on 2000 test images with fixed noise levels
    with torch.no_grad():
        gg = torch.Generator().manual_seed(1)
        x0 = test[:2000].to(DEV); t = torch.randint(1, T + 1, (2000,), generator=gg).to(DEV)
        eps = torch.randn(x0.shape, generator=gg).to(DEV); a, b = coeffs(ABAR.float().to(DEV), t)
        held = F.mse_loss(ema(a * x0 + b * eps, t), eps).item()
    log(f"  held-out simple loss (EMA weights, 2000 test images): {held:.4f}")
    return ema, test, nparam, held


def digits_outputs(ema, test):
    out = {}
    torch.manual_seed(SEED + 1)
    # the forward chain for two test digits: one coupled trajectory each, x_t = sqrt(alpha_t) x_{t-1} + sqrt(1 - alpha_t) eta_t
    pick = [0, 1]      # a 7 and a 2 (the first two test images)
    x = test[pick].double()
    chain = [x.numpy().copy()]
    for t in range(1, T + 1):
        x = ALPHA[t - 1].sqrt() * x + (1 - ALPHA[t - 1]).sqrt() * torch.randn_like(x)
        if t % 10 == 0: chain.append(x.numpy().copy())
    out["chain"] = {"every": 10, "images": pack4(np.stack(chain, 1))}          # 2 digits x 101 frames
    # independent draws from q(x_t | x0) for the first digit, at the schedule slide's levels
    lv = [0, 50, 100, 200, 300, 500, 700, 1000]
    x0 = test[0].double()
    draws = [x0.numpy()] + [(ABAR[t - 1].sqrt() * x0 + (1 - ABAR[t - 1]).sqrt() * torch.randn(784, dtype=torch.float64)).numpy() for t in lv[1:]]
    out["marginal"] = {"t": lv, "images": pack4(np.stack(draws))}
    # x_t = a_t x0 + b_t eps for one test digit at t = 300, and the network's clean predictions at several levels (same eps)
    x0 = test[3].to(DEV); eps = torch.randn(784, generator=torch.Generator().manual_seed(7)).to(DEV)
    xts, preds = [], []
    with torch.no_grad():
        for t in PRED_T:
            a, b = math.sqrt(ABAR[t - 1]), math.sqrt(1 - ABAR[t - 1])
            xt = a * x0 + b * eps
            e = ema(xt[None], torch.tensor([t], device=DEV))[0]
            xts.append(xt.cpu().numpy()); preds.append(((xt - b * e) / a).cpu().numpy())
    out["predict"] = {"t": PRED_T, "x0": pack4(x0.cpu().numpy()), "eps": pack4(eps.cpu().numpy()),
                      "xt": pack4(np.stack(xts)), "pred": pack4(np.stack(preds)),
                      "a": [round(math.sqrt(ABAR[t - 1]), 4) for t in PRED_T], "b": [round(math.sqrt(1 - ABAR[t - 1]), 4) for t in PRED_T]}
    # generation: N_GEN chains from x_T ~ N(0, I); x_t kept at FRAMES, and the clean prediction along chain 0
    torch.manual_seed(SEED + 2)
    xT = torch.randn(N_GEN, 784, device=DEV)
    xs, pr = ancestral(ema, xT, BETA, keep=set(FRAMES), pred_for=0)
    out["generate"] = {"frames": FRAMES, "n": N_GEN, "images": pack4(np.stack([xs[f] for f in FRAMES], 1)),
                       "pred0": pack4(np.stack([pr[f] for f in FRAMES]))}
    return out


def gmm_sample(n, g):
    k = torch.randint(0, 2, (n,), generator=g)
    m = torch.tensor(MODES, dtype=torch.float32)[k]
    return m + MODE_SD * torch.randn(n, 2, generator=g)


def gmm_mean_x0(xt, a, b):
    """the exact E[x0 | x_t] for the two-mode data (both modes weight 1/2, isotropic sd MODE_SD)"""
    m = np.array(MODES); v = a * a * MODE_SD ** 2 + b * b
    logw = np.stack([-((xt - a * mk) ** 2).sum(1) / (2 * v) for mk in m], 1)
    w = np.exp(logw - logw.max(1, keepdims=True)); w /= w.sum(1, keepdims=True)
    post = [mk + (a * MODE_SD ** 2 / v) * (xt - a * mk) for mk in m]
    return w[:, :1] * post[0] + w[:, 1:] * post[1]


def two_d(log):
    torch.manual_seed(SEED)
    g = torch.Generator().manual_seed(SEED)
    net = MLP()
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 30000)
    run = 0.0
    for k in range(1, 30001):
        x0 = gmm_sample(512, g)
        t = torch.randint(1, T2 + 1, (512,), generator=g)
        a, b = coeffs(ABAR2, t)
        eps = torch.randn(512, 2, generator=g)
        loss = F.mse_loss(net(a * x0 + b * eps, t), eps)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        run += loss.item()
        if k % 10000 == 0: log(f"  two-d update {k}: mean loss {run / 10000:.4f}"); run = 0.0
    net.eval()
    out = {"T": T2, "modes": MODES, "sd": MODE_SD, "beta": [1e-3, 0.15]}
    data = gmm_sample(400, torch.Generator().manual_seed(11))
    out["data"] = np.round(data.numpy(), 3).tolist()
    # generation: 400 chains, every second level kept
    torch.manual_seed(12)
    keep = set(range(0, T2 + 1, 2))
    xs, _ = ancestral(net, torch.randn(400, 2), BETA2, keep=keep)
    traj = np.stack([xs[t] for t in sorted(keep, reverse=True)], 0)          # (51, 400, 2), from t = T down to 0
    out["generate"] = {"every": 2, "points": base64.b64encode(np.clip(np.rint(traj * 1000), -32767, 32767).astype("<i2").tobytes()).decode()}
    # clean predictions at several noise levels, for points drawn from q(x_t | x0); also the exact conditional mean
    lv = [int(t) for t in np.searchsorted((1 - ABAR2).numpy(), [0.04, 0.2, 0.5, 0.8, 0.95]) + 1]
    gg = torch.Generator().manual_seed(13)
    pts, dev = [], []
    for t in lv:
        x0 = gmm_sample(150, gg); a, b = math.sqrt(ABAR2[t - 1]), math.sqrt(1 - ABAR2[t - 1])
        xt = a * x0 + b * torch.randn(150, 2, generator=gg)
        with torch.no_grad(): xh = (xt - b * net(xt, torch.full((150,), t))) / a
        exact = gmm_mean_x0(xt.numpy().astype(np.float64), a, b)
        dev.append(float(np.sqrt(((xh.numpy() - exact) ** 2).sum(1)).mean()))
        pts.append({"t": t, "a": round(a, 4), "b": round(b, 4), "xt": np.round(xt.numpy(), 3).tolist(), "pred": np.round(xh.numpy(), 3).tolist()})
    out["predict"] = pts
    log("  two-d levels " + ", ".join(f"t={p['t']} (b^2={p['b'] ** 2:.2f}): mean distance to exact E[x0|x_t] {d:.3f}" for p, d in zip(pts, dev)))
    end = traj[-1]
    near = [int((np.linalg.norm(end - np.array(m), axis=1) < 3 * MODE_SD).sum()) for m in MODES]
    log(f"  two-d generated: {near[0]} near mode 1, {near[1]} near mode 2, of 400")
    out["check"] = {"nearModes": near, "predDev": [round(d, 4) for d in dev]}
    return out


def main():
    pilot = len(sys.argv) > 1 and sys.argv[1] == "pilot"
    logf = open(HERE / ("pilot.log" if pilot else "run.log"), "w")
    def log(s):
        print(s, flush=True); logf.write(s + "\n"); logf.flush()
    log(time.strftime("%Y-%m-%d %H:%M") + "  " + " ".join(sys.argv))
    ema, test, nparam, held = train_digits(log, 300 if pilot else STEPS)
    if pilot: return
    res = {"setup": {"T": T, "beta": [1e-4, 0.02], "updates": STEPS, "batch": BATCH, "lr": LR, "ema": EMA, "params": nparam,
                     "heldOutLoss": round(held, 4), "seed": SEED}}
    res["digits"] = digits_outputs(ema, test)
    res["twod"] = two_d(log)
    (HERE / "diffusion.json").write_text(json.dumps(res, separators=(",", ":")))
    log(f"wrote diffusion.json ({(HERE / 'diffusion.json').stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
