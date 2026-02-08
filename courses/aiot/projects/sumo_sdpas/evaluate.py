

"""
evaluate.py — Run inference with a trained DQN/SARSA policy on the SUMO environment.

Usage
-----
$ python evaluate.py --model weights_500ep.pth --episodes 5 --csv results/eval_metrics.csv

Features
--------
* Re‑uses `TrafficEnv`, `QNetwork`, `CFG`, and `ACTIONS` from *train.py* (import‑safe).
* Runs greedy policy (ε = 0) for a given number of episodes.
* Prints per‑episode reward / mean waiting time and aggregates average stats.
* Optionally writes a CSV with metrics for further analysis.

Note:  Make sure the model width (`hidden_dim`) here matches the one used in training
       (currently 256).  Adjust if you changed it.
"""
from __future__ import annotations

import argparse
import csv
import datetime
from pathlib import Path

import numpy as np
import torch

# ---- Import training definitions without re‑running training --------------
import train as tr  # train.py is expected in the same directory

# -- Sanity‑check: importing train does NOT trigger training, because
#    its `main()` call is guarded by `if __name__ == "__main__":`.

# ------------------------------------------------------------------------- #


def evaluate(model_path: str, episodes: int = 10, csv_out: str | None = None):
    """Run <episodes> evaluation episodes and report metrics."""
    device = tr.CFG.DEVICE
    # ---- Re‑create policy network -----------------------------------------
    input_dim = 4  # ns, ew, phase, elapsed — must match train.py
    hidden_dim = 256  # keep in sync with training script
    output_dim = len(tr.ACTIONS)

    policy_net = tr.QNetwork(input_dim, hidden_dim, output_dim).to(device)
    ckpt = torch.load(model_path, map_location=device)
    policy_net.load_state_dict(ckpt)
    policy_net.eval()

    rewards: list[float] = []
    mean_waits: list[float] = []

    env = tr.TrafficEnv()
    for ep in range(episodes):
        state = env.reset()
        total_r = 0.0
        waits_ep: list[float] = []

        while True:
            s_tensor = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
            with torch.no_grad():
                q_vals = policy_net(s_tensor)
            action = q_vals.argmax(1).item()  # greedy
            next_state, r, done = env.step(action)

            total_r += r
            waits_ep.append(env.state_wait)
            state = next_state
            if done:
                break

        rewards.append(total_r)
        mean_wait = float(np.mean(waits_ep)) if waits_ep else 0.0
        mean_waits.append(mean_wait)
        print(f"[Eval] Episode {ep+1}/{episodes} — reward: {total_r:.2f}, mean_wait: {mean_wait:.1f}s")

    env.close()

    avg_reward = float(np.mean(rewards))
    avg_wait   = float(np.mean(mean_waits))
    print("\n========== Evaluation Summary ==========")
    print(f"  Episodes        : {episodes}")
    print(f"  Avg. Reward     : {avg_reward:.2f}")
    print(f"  Avg. Mean Wait  : {avg_wait:.1f}s")
    print("========================================")

    # ---- Optionally write CSV ----------------------------------------------
    if csv_out:
        csv_path = Path(csv_out)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["episode", "total_reward", "mean_wait"])
            for idx, (r, w) in enumerate(zip(rewards, mean_waits), 1):
                writer.writerow([idx, f"{r:.4f}", f"{w:.2f}"])
        print(f"[Eval] Metrics saved → {csv_path.as_posix()}")


# ------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained SUMO RL policy.")
    parser.add_argument(
        "--model",
        required=True,
        help="Path to the trained policy .pth file (state_dict).",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Optional path to write episode‑level metrics CSV.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch evaluation in SUMO‑GUI instead of the CLI binary."
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=1,
        help="Number of evaluation episodes to run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # ------------------------------------------------------------------
    # If --gui is given, tell TrafficEnv to use the graphical SUMO build
    if args.gui:
        tr.SUMO_BINARY = "sumo-gui"        # override global used by TrafficEnv
        print("[Eval] SUMO GUI mode activated.")
    # ------------------------------------------------------------------
    if not Path(args.model).is_file():
        raise FileNotFoundError(f"Model checkpoint '{args.model}' not found.")
    evaluate(args.model, args.episodes, args.csv)


if __name__ == "__main__":
    main()
