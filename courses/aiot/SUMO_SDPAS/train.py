"""
train.py — Reinforcement Learning for SUMO Traffic Signal Control(quiet mode)

主要功能 (Features)
------------------
1. 以 **SUMO + TraCI** 模擬單一路口車流，動態讀取受控車道並自動分群 (NS / EW)。
2. 實作 **DQN / SARSA** 演算法：經驗回放、目標網路同步，以及 ε‑greedy / SARSA 策略更新。
3. 自訂化獎勵函式：等待時間差分 + 變燈懲罰，並支援最小綠燈時段約束。
4. 訓練過程自動產生日誌與圖表 (`training_logs/`)：CSV 指標、Loss / Waiting / Q‑Value / ε 曲線。
5. 完整隨機種子設定，保證實驗 **可重現**。
"""

from pathlib import Path  # noqa: E402  (ensure Path is available early)

# === Resolve project directory and default asset paths ===
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SUMO_CONFIG = (SCRIPT_DIR / "SumoData/osm.sumocfg").as_posix()
DEFAULT_ROUTE_FILES = [
    (SCRIPT_DIR / "SumoData/osm.passenger.rou.xml").as_posix(),
    (SCRIPT_DIR / "SumoData/osm.rou.xml").as_posix(),
]

# === 1. Imports & Dependencies ===
import os
import logging
import csv
import contextlib
import random
from collections import deque

import numpy as np
import traci
from traci.exceptions import TraCIException
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.cuda.amp as amp
# parallel environment helper
from parallel_env import MultiprocessingTrafficEnv
# CLI and path helpers
import datetime

# ------------- Automatic route sanitization -----------------

import xml.etree.ElementTree as ET
import tempfile
try:
    import sumolib  # part of SUMO tools; used to read network
except ImportError:
    sumolib = None  # handle gracefully

# --- Emergency route edge collector ---
def get_ambulance_edges(route_files: list[str]) -> set[str]:
    """
    Parse the given .rou.xml files and return a set of edge IDs that are part
    of any ambulance / emergency vehicle route.  Detects via either
    vClass="emergency"  **or**  id prefix that contains 'ambulance'.
    """
    amb_edges: set[str] = set()
    for rf in route_files:
        try:
            tree = ET.parse(rf)
        except Exception:
            continue
        for veh in tree.findall(".//vehicle"):
            vclass = veh.attrib.get("vClass", "")
            vid    = veh.attrib.get("id", "")
            is_amb = (vclass == "emergency") or ("ambulance" in vid.lower())
            if not is_amb:
                continue
            route_elem = veh.find("route")
            if route_elem is not None:
                amb_edges.update(route_elem.attrib.get("edges", "").split())
    return amb_edges

def _get_net_path(sumocfg_path: str) -> str | None:
    """Parse the .sumocfg XML and return the referenced net-file path."""
    try:
        tree = ET.parse(sumocfg_path)
        net_elem = tree.find(".//input/net-file")
        if net_elem is None:
            return None
        net_path = (Path(sumocfg_path).parent / net_elem.attrib["value"]).as_posix()
        return net_path
    except Exception:  # noqa: BLE001
        return None

def sanitize_route(net_path: str, route_path: str) -> str:
    """
    Remove vehicles / routes that reference unknown edges so SUMO can load without error.
    Returns the path to a (possibly new) route file guaranteed to be network‑compatible.
    """
    if sumolib is None or not Path(net_path).is_file():
        # Cannot verify – return original
        return route_path

    net = sumolib.net.readNet(net_path, withInternal=True)
    valid_edges = set(e.getID() for e in net.getEdges())
    tree = ET.parse(route_path)
    root = tree.getroot()
    removed = 0

    # --- helper to decide if an edge sequence is valid ---
    def _edges_ok(edge_str: str) -> bool:
        return all(e in valid_edges for e in edge_str.strip().split())

    # filter <vehicle> that embed <route edges="">
    for veh in list(root.findall(".//vehicle")):
        route_elem = veh.find("route")
        if route_elem is not None and not _edges_ok(route_elem.attrib.get("edges", "")):
            root.remove(veh)
            removed += 1

    # filter standalone <route>
    for rte in list(root.findall(".//route")):
        if not _edges_ok(rte.attrib.get("edges", "")):
            root.remove(rte)
            removed += 1

    if removed == 0:
        return route_path  # original is fine

    # write sanitized version to a temp file in the same directory
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="sanitized_", suffix=".rou.xml",
                                        dir=Path(route_path).parent)
    os.close(tmp_fd)  # close low‑level fd
    tree.write(tmp_path, encoding="utf-8")
    print(f"[sanitize_route] Removed {removed} invalid routes → {tmp_path}")
    return tmp_path

# === Global Hyperparameter Configuration ===
class CFG:
    # --- Reproducibility ---
    SEED = 42

    # --- DQN hyperparameters ---
    BUFFER_CAPACITY = 100000   # replay buffer size
    BATCH_SIZE      = 1024   # leverage 12 GB VRAM; lower if OOM
    LR_DQN          = 1e-3    # slightly higher learning rate
    TARGET_UPDATE   = 500      # steps between target-net sync
    GAMMA           = 0.98     # discount factor

    # --- Traffic signal constraints ---
    MIN_GREEN_STEPS = 5        # minimum green duration to avoid flicker

    # --- Reward shaping ---
    C_REWARD       = 10.0
    PENALTY_SWITCH = 5

    # --- Algorithm choice ---
    USE_SARSA = True

    # --- Episode control ---
    MAX_STEPS  = 300     # reduced from 500
    EPS_INIT   = 1.0
    EPS_MIN    = 0.1
    EPS_DECAY  = 0.995

    # --- Parallel environments ---
    NUM_ENVS = 1

    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ----- Unified default paths & run control -----
    SUMO_BINARY  = os.getenv("SUMO_BINARY", "sumo")
    SUMO_CONFIG  = DEFAULT_SUMO_CONFIG
    ROUTE_FILES  = DEFAULT_ROUTE_FILES        # accept multiple route files
    TL_ID = [
        "cluster_5066556756_662312633_662315056_662315165",
        "cluster_10156051673_4539158625_6654202315_7578670184_#1more",
        "cluster_1140217849_5813479945",
        "cluster_11786506848_1215000588_6395490542",
        "cluster_1223757527_7578670286_7578670388",
        "cluster_12565503452_12565503454_2612435156_4539077690",
        "cluster_1505012124_5192834728",
        "cluster_1672906043_2613505701_2613505703_2613505709_#2more",
        "cluster_1720485436_4525805668_4539051860_4539051865",
        "cluster_1720485444_4525805659_5247483238_5247483239_#1more",
        "cluster_1720485456_4493660362_5247483226",
        "cluster_181182963_4525670543",
        "cluster_2043097290_4514855867_5203841902_7782558075_#1more",
        "cluster_2046348191_2050931381_6395490540_6395490541_#2more",
        "cluster_2088253314_2612435147_2618719343_2897253187_#4more",
        "cluster_2112377011_7578670295_7578670296_7578670297_#1more",
        "cluster_2341918921_7723501602_7723501605",
        "cluster_244380262_965533199",
        "cluster_2485874904_655375241_655375242",
        "cluster_2507433120_3799089093_5141544838_5141544839",
        "cluster_260240791_260240818_4514856052_4882797242",
        "cluster_260240793_5849716126_5849716127_5875366026",
        "cluster_2609618892_4539076377_4539076387_7578670186",
        "cluster_2612435143_4539166738",
        "cluster_2612435149_5707432605_6397118917_7578670189_#1more",
        "cluster_2612435166_4514856053_4990873860_4990873865",
        "cluster_2618719325_6654202352",
        "cluster_2644088350_280389390_5203807318_5246620218",
        "cluster_2749386139_2749386141",
        "cluster_2751243356_8140710018_8141908747",
        "cluster_2751243367_5203807727_6654202321_6654202378_#2more",
        "cluster_2766951689_5247481910_7578670194",
        "cluster_2836052472_6654202324_6654202325",
        "cluster_3039147936_5781854195",
        "cluster_3263854359_5141525250_5141525252_5141544845",
        "cluster_346114655_4202524123",
        "cluster_3799089094_3799089095_4872638613_6381028700_#1more",
        "cluster_385076470_4260908428_662368087_7578670288_#2more",
        "cluster_4335733872_5987407032_656416110",
        "cluster_4493660353_5247483208_9402583774",
        "cluster_4510426998_4510427018_5246620165_5246620166_#4more",
        "cluster_4514945003_5246621626_5246621630_9402530954",
        "cluster_4525797449_5813516453_5813516455_5813516456_#3more",
        "cluster_4539076369_4539077695_7723457872_912964558",
        "cluster_4539076372_7578670203_760893504_7782558078_#3more",
        "cluster_4539077696_912965413",
        "cluster_4539162229_760893582_7723489131",
        "cluster_4864772557_638213093",
        "cluster_5141544847_912964561",
        "cluster_5203807736_6654202322_6654202323_7782558068_#3more",
        "cluster_5203841904_7782558076",
        "cluster_5246606009_5246606055_662162026_662162030_#2more",
        "cluster_5246620180_5246620187_9402558757_965533218",
        "cluster_648173104_7702094887_7702094891",
        "cluster_656415975_7702094922_7702094923",
        "cluster_656416041_7578663863_7578663864",
        "cluster_656416106_7578663866_7578663867_7578663868",
        "cluster_656416199_7578670048_7578670051_7702095011",
        "cluster_662314604_662314612_7052731755_7723490408_#1more",
        "cluster_6654202330_6654202331_6654202365_911593397",
    ]
    EPISODES      = 1000     # reduced from 1000
    RUN_ID       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    NET_FILE     = None
    SEED_OFFSET  = 0
# ---------------------- Reproducibility ---------------------- #
random.seed(CFG.SEED)
np.random.seed(CFG.SEED)
torch.manual_seed(CFG.SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(CFG.SEED)
# --- Performance tuners ----------------------------------------------------
torch.backends.cudnn.benchmark = True          # autotune kernels for fixed shapes
torch.set_num_threads(os.cpu_count())          # use all CPU cores
# -------------------------------------------------------------------------- #


# === DQN and Replay Buffer ===


class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    def push(self, s, a, r, s_next, done):
        self.buffer.append((s, a, r, s_next, done))
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        s, a, r, s_next, d = map(np.stack, zip(*batch))
        return (torch.tensor(s, dtype=torch.float32, device=CFG.DEVICE),
                torch.tensor(a, dtype=torch.int64,   device=CFG.DEVICE),
                torch.tensor(r, dtype=torch.float32, device=CFG.DEVICE),
                torch.tensor(s_next, dtype=torch.float32,device=CFG.DEVICE),
                torch.tensor(d, dtype=torch.float32, device=CFG.DEVICE))
    def __len__(self):
        return len(self.buffer)

class QNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    def forward(self, x):
        return self.net(x)

# ---- Lane lists are now built dynamically after SUMO loads ----
# They are kept here only as global placeholders for modules that
# might import them.  TrafficEnv will populate them at runtime.
NS_LANES, EW_LANES, LANES = [], [], []

ACTIONS = [0, 2]  # 0=EW, 2=NS


def reward_delta(prev_wait, curr_wait, prev_phase, curr_phase):
    """
    根據前後等待時間的差異計算平滑化獎勵，並加入號誌切換的懲罰。
    Args:
        prev_wait (float): 先前累積等待時間
        curr_wait (float): 目前累積等待時間
        prev_phase (int): 先前的號誌相位
        curr_phase (int): 目前的號誌相位
    Returns:
        float: 加上懲罰後的平滑化獎勵值
    """
    raw = prev_wait - curr_wait
    # smooth reward: raw / (raw + C)
    r = raw / (abs(raw) + CFG.C_REWARD)
    # penalty for switching
    if curr_phase != prev_phase:
        r -= CFG.PENALTY_SWITCH / CFG.C_REWARD
    return r

# ------------------------------ 基本設定 ------------------------------
# Use CFG for unified defaults
SUMO_BINARY  = CFG.SUMO_BINARY
SUMO_CONFIG  = CFG.SUMO_CONFIG
TL_ID_LIST   = CFG.TL_ID if isinstance(CFG.TL_ID, (list, tuple)) else [CFG.TL_ID]
TL_ID        = TL_ID_LIST[0]   # placeholder; TrafficEnv may override

ROUTE_FILES  = CFG.ROUTE_FILES   # list of .rou.xml files

# --- Collect ambulance route edges at startup ---
AMB_EDGES = get_ambulance_edges(ROUTE_FILES)

LANES = LANES

NUM_EPISODES = CFG.EPISODES

# Allow SUMO to continue even if some routes become invalid during simulation
SUMO_EXTRA_ARGS = ["--ignore-route-errors"]


# === Simplified State Extraction ===
# (get_state() removed)

#
# ------------ Emergency helpers -------------------------------------------------
def set_full_red(tls_id: str, duration: int = 3):
    """
    Force the given traffic light into an all‑red phase for <duration> seconds.
    Args:
        tls_id   (str): Traffic‑light system ID.
        duration (int): How many simulation seconds to keep all signals red.
    """
    n_links = len(traci.trafficlight.getControlledLinks(tls_id))
    traci.trafficlight.setRedYellowGreenState(tls_id, "r" * n_links)
    # Let SUMO hold this phase for the specified duration
    traci.trafficlight.setPhaseDuration(tls_id, duration)

def clear_full_red(tls_id: str):
    """
    Exit the temporary all‑red phase and resume the programmed logic.
    """
    traci.trafficlight.setPhaseDuration(tls_id, 0)   # jump to next phase

def handle_emergency_blockage(veh_id: str, wait_thr: float = 3.0, occupy_time: int = 30):
    """
    If the emergency vehicle <veh_id> is blocked (> wait_thr s), temporarily
    move it to the opposite lane (laneIndex = -1).  Fallback to re‑routing
    when lane change is impossible.
    """
    try:
        w = traci.vehicle.getWaitingTime(veh_id)
        if w > wait_thr:
            # Try opposite lane first
            current_lane = traci.vehicle.getLaneID(veh_id)
            opp_lane_index = -1
            traci.vehicle.changeLane(veh_id, opp_lane_index, occupy_time)
    except traci.TraCIException:
        # Opposite lane unavailable → let SUMO compute fastest detour
        try:
            traci.vehicle.rerouteTraveltime(veh_id)
        except traci.TraCIException:
            # Ignore if re‑route also fails (e.g., vehicle has arrived)
            pass
# ------------------------------------------------------------------------------- 

# === 2a. Traffic Environment Wrapper ===
class TrafficEnv:
    """
    Gym-style wrapper for SUMO & TraCI:
    - reset(): restart simulation and return initial obs
    - step(action_idx): apply action, advance sim, return (obs, reward, done)
    """
    def __init__(self):
        cmd = [SUMO_BINARY, "-c", SUMO_CONFIG, "--no-step-log", "--no-warnings", *SUMO_EXTRA_ARGS]
        # Comment out or remove repeated route-file lines
        # for rf in ROUTE_FILES:
        #     cmd += ["-r", rf]
        traci.start(cmd)
        # ------------------------------------------------------------------
        # Validate TL_ID against the current network; auto‑fallback if needed
        tls_ids = traci.trafficlight.getIDList()
        global TL_ID
        selected = None
        # --- 1) respect user-provided list if possible -------------------------
        if isinstance(CFG.TL_ID, (list, tuple)):
            for cand in CFG.TL_ID:
                if cand in tls_ids:
                    selected = cand
                    break
        elif isinstance(CFG.TL_ID, str) and CFG.TL_ID in tls_ids:
            selected = CFG.TL_ID
        # --- 2) fallback to automatic relevance / busiest selection ------------
        if selected is None:
            def tl_relevant(tl):
                lanes = traci.trafficlight.getControlledLanes(tl)
                edges = {ln.split("_")[0] for ln in lanes}
                return not AMB_EDGES.isdisjoint(edges)
            relevant_tls = [tl for tl in tls_ids if tl_relevant(tl)]
            if relevant_tls:
                selected = max(relevant_tls, key=lambda tl: len(traci.trafficlight.getControlledLanes(tl)))
            else:
                selected = max(tls_ids, key=lambda tl: len(traci.trafficlight.getControlledLanes(tl)))
        TL_ID = selected
        # ------------------------------------------------------------------
        # Dynamically retrieve and categorize the TL‑controlled lanes
        controlled = list(dict.fromkeys(traci.trafficlight.getControlledLanes(TL_ID)))  # unique, ordered
        def _is_ew(lid):
            # Use lane angle in degrees (0 = east, 90 = north)
            ang = traci.lane.getAngle(lid)
            ang_mod = (ang + 360.0) % 180.0    # fold to [0,180)
            return ang_mod < 45.0 or ang_mod > 135.0
        self.ew_lanes = [ln for ln in controlled if _is_ew(ln)]
        self.ns_lanes = [ln for ln in controlled if ln not in self.ew_lanes]
        self.lanes    = self.ns_lanes + self.ew_lanes
        # expose to module‑level globals for convenience
        global NS_LANES, EW_LANES, LANES
        NS_LANES, EW_LANES, LANES = self.ns_lanes, self.ew_lanes, self.lanes
        lane_sub_vars = [traci.constants.LAST_STEP_VEHICLE_NUMBER]
        for ln in self.lanes:
            traci.lane.subscribe(ln, lane_sub_vars)
        self.last_switch = 0
        self.step_count = 0
        self.state_wait = sum(traci.lane.getWaitingTime(l) for l in self.lanes)

    def reset(self):
        cmd = ["-c", SUMO_CONFIG]
        # Comment out or remove repeated route-file lines
        # for rf in ROUTE_FILES:
        #     cmd += ["-r", rf]
        cmd += ["--no-step-log", "--no-warnings", *SUMO_EXTRA_ARGS]
        traci.load(cmd)
        lane_sub_vars = [traci.constants.LAST_STEP_VEHICLE_NUMBER]
        for ln in self.lanes:
            traci.lane.subscribe(ln, lane_sub_vars)
        self.last_switch = 0
        self.step_count = 0
        self.state_wait = sum(traci.lane.getWaitingTime(l) for l in self.lanes)
        return self._get_obs()

    def _get_obs(self):
        ns = sum(
            traci.lane.getSubscriptionResults(l)[traci.constants.LAST_STEP_VEHICLE_NUMBER]
            for l in self.ns_lanes
        )
        ew = sum(
            traci.lane.getSubscriptionResults(l)[traci.constants.LAST_STEP_VEHICLE_NUMBER]
            for l in self.ew_lanes
        )
        raw_phase = traci.trafficlight.getPhase(TL_ID)
        # Map SUMO phases (0‒1 = EW green/yellow, 2‒3 = NS green/yellow) to a
        # canonical major phase index: 0 = EW, 1 = NS
        major_phase = 0 if raw_phase < 2 else 1
        elapsed     = self.step_count - self.last_switch
        elapsed_norm = elapsed / CFG.MAX_STEPS
        phase_norm  = major_phase / (len(ACTIONS) - 1)  # 0.0 or 1.0
        # normalize features
        ns_norm = ns / 100.0
        ew_norm = ew / 100.0
        return (ns_norm, ew_norm, phase_norm, elapsed_norm)

    def step(self, action_idx):
        obs = self._get_obs()
        try:
            # --- enforce minimum green duration ---------------------------------
            current_raw_phase   = traci.trafficlight.getPhase(TL_ID)
            current_major_phase = 0 if current_raw_phase < 2 else 1   # 0→EW, 1→NS
            current_action_idx  = current_major_phase                 # aligns with ACTIONS index

            elapsed_since_switch = self.step_count - self.last_switch
            if elapsed_since_switch < CFG.MIN_GREEN_STEPS:
                # Not enough time has elapsed → stay on current phase
                action_idx = current_action_idx
            else:
                # Allowed to switch; record switch time if phase changes
                if action_idx != current_action_idx:
                    self.last_switch = self.step_count

            real_phase = ACTIONS[action_idx]
            traci.trafficlight.setPhase(TL_ID, real_phase)
            for _ in range(50):     # increased from 30
                traci.simulationStep()

            next_obs = self._get_obs()
            curr_wait = sum(traci.lane.getWaitingTime(l) for l in self.lanes)
            # unified reward
            r = reward_delta(self.state_wait, curr_wait, current_action_idx, action_idx)
            self.state_wait = curr_wait
            self.step_count += 1
            done = (traci.simulation.getMinExpectedNumber() == 0 or self.step_count >= CFG.MAX_STEPS)
            return next_obs, r, done
        except TraCIException as e:
            logging.error(f"TraCI error in step(): {e}")
            # Stop simulation gracefully; signal episode termination
            return obs, 0.0, True

    def close(self):
        traci.close()

# --------------------------- 輔助函式 ---------------------------

@contextlib.contextmanager
def suppress_output():
    """Redirect *process-level* FD 1/2 to /dev/null (covers C-level prints)."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    # 保存原始 fd
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        # 恢復原始 fd
        os.dup2(old_stdout_fd, 1)
        os.dup2(old_stderr_fd, 2)
        os.close(old_stdout_fd)
        os.close(old_stderr_fd)
        os.close(devnull)

# ------------------------------ Episode ------------------------------

# === 4. Episode Runner ===
# Executes one training episode: state encoding, action selection, simulation steps, and weight updates.
def run_episode(policy_net, target_net, buffer, optimizer, episode_id, log, eps, step_count, scaler, num_envs: int = 1):
    """
    執行單一訓練回合:
    1) 取得初始 state
    2) 依照 ε-greedy 策略選擇動作
    3) 進行數個 SUMO 步驟後獲得新 state 與獎勵
    4) 將資料推進 ReplayBuffer
    5) 根據樣本進行 DQN 參數更新
    Args:
        policy_net (nn.Module): 主要 Q-network
        target_net (nn.Module): 用於穩定訓練的目標 Q-network
        buffer (ReplayBuffer): 經驗回放緩衝區
        optimizer (torch.optim.Optimizer): 最佳化函式
        episode_id (int): 当前訓練回合編號
        log (list): 用於存放每回合總獎勵的清單
        eps (float): ε-greedy 中的 ε 值
        step_count (int): 累積訓練步數計數器
        scaler (amp.GradScaler): 混合精度縮放器
    Returns:
        int: 更新後的步數計數器
    """
    if num_envs > 1:
        env = MultiprocessingTrafficEnv(num_envs)
        states = env.states
    else:
        env = TrafficEnv()
        states = [env.reset()]

    total_reward = [0.0 for _ in range(num_envs)]
    waits = [[] for _ in range(num_envs)]
    q_vals = [[] for _ in range(num_envs)]
    losses = []  # collect per‑update loss values

    dones = [False for _ in range(num_envs)]

    while not all(dones):
        s_tensor = torch.tensor(states, dtype=torch.float32, device=CFG.DEVICE)
        with torch.no_grad():
            q_pred = policy_net(s_tensor)
        actions = []
        for i in range(num_envs):
            q_vals[i].append(q_pred[i].max().item())
            if random.random() < eps:
                actions.append(random.randrange(len(ACTIONS)))
            else:
                actions.append(q_pred[i].argmax().item())

        try:
            if num_envs > 1:
                next_states, rewards, step_dones, wait_list = env.step(actions)
            else:
                ns, r, d = env.step(actions[0])
                next_states, rewards, step_dones = [ns], [r], [d]
                wait_list = [env.state_wait]
        except TraCIException as e:
            logging.error(f"TraCIException during episode {episode_id}: {e}")
            break

        for i in range(num_envs):
            buffer.push(states[i], actions[i], rewards[i], next_states[i], step_dones[i])
            total_reward[i] += rewards[i]
            waits[i].append(wait_list[i])
            dones[i] = step_dones[i]

        states = next_states
        # DQN update
        if len(buffer) >= CFG.BATCH_SIZE:
            s_b, a_b, r_b, s2_b, d_b = buffer.sample(CFG.BATCH_SIZE)
            q_preds = policy_net(s_b).gather(1, a_b.unsqueeze(1)).squeeze(1)
            with torch.no_grad():
                if CFG.USE_SARSA:
                    next_q_all = policy_net(s2_b)
                    next_actions = next_q_all.argmax(1, keepdim=True)
                    q_next = next_q_all.gather(1, next_actions).squeeze(1)
                else:
                    q_next = target_net(s2_b).max(1)[0]
                q_target = r_b + CFG.GAMMA * q_next * (1 - d_b)
            with amp.autocast():
                loss = F.mse_loss(q_preds, q_target)
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            losses.append(loss.item())
            if step_count % CFG.TARGET_UPDATE == 0:
                target_net.load_state_dict(policy_net.state_dict())
        step_count += num_envs

    env.close()
    mean_reward = sum(total_reward) / num_envs
    log.append(mean_reward)
    mean_loss = sum(losses) / len(losses) if losses else 0.0
    mean_wait = sum(sum(w) / len(w) if w else 0.0 for w in waits) / num_envs
    mean_q = sum(sum(q) / len(q) if q else 0.0 for q in q_vals) / num_envs
    return step_count, mean_reward, mean_loss, mean_wait, mean_q

# === 5. Training Loop (main) ===
# Orchestrates multiple episodes, updates hyperparameters, and logs metrics.
def main():
    """
    執行主要訓練流程:
    1) 設定並初始化網路、緩衝區與參數
    2) 依據設定之回合數，重覆執行訓練流程
    3) 當獎勵表現提升時，適度衰減 ε 值
    4) 記錄日誌與產生學習曲線
    """
    global SUMO_BINARY, SUMO_CONFIG, ROUTE_FILES, NUM_EPISODES, TL_ID
    SUMO_BINARY  = CFG.SUMO_BINARY
    SUMO_CONFIG  = CFG.SUMO_CONFIG
    ROUTE_FILES  = CFG.ROUTE_FILES
    TL_ID        = CFG.TL_ID
    NUM_EPISODES = CFG.EPISODES
    run_id       = CFG.RUN_ID
    # -- checkpoint filenames -------------------------------------------
    best_ckpt_path  = Path("training_logs") / run_id / "policy_best.pth"
    final_ckpt_path = Path("training_logs") / run_id / "policy_final.pth"
    if not Path(SUMO_CONFIG).is_file():
        raise FileNotFoundError(f"SUMO config file '{SUMO_CONFIG}' not found — use CFG.SUMO_CONFIG to specify a different one.")
    if CFG.SEED_OFFSET != 0:
        torch.manual_seed(CFG.SEED + CFG.SEED_OFFSET)
        np.random.seed(CFG.SEED + CFG.SEED_OFFSET)
        random.seed(CFG.SEED + CFG.SEED_OFFSET)

    # --- skipping route sanitization to preserve all vehicles ---
    if CFG.NET_FILE:
        net_path = CFG.NET_FILE
    else:
        net_path = _get_net_path(SUMO_CONFIG)
    # Keep original route files
    ROUTE_FILES = CFG.ROUTE_FILES

    # ensure logging directory exists *before* configuring FileHandler
    log_dir = Path("training_logs") / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir/"train.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # metrics CSV
    csv_path = str(log_dir/"metrics.csv")
    csv_file = open(csv_path, "w", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        "episode", "total_reward", "mean_loss", "mean_wait", "mean_q", "epsilon",
        "num_edges", "num_lanes", "total_lane_length"
    ])
    metrics_rows = []

    # gather static network info via SUMO
    env_static = TrafficEnv()
    num_edges = len(traci.edge.getIDList())
    num_lanes = len(traci.lane.getIDList())
    total_lane_length = sum(traci.lane.getLength(l) for l in traci.lane.getIDList())
    env_static.close()

    input_dim = 4  # ns, ew, phase, elapsed
    policy_net = QNetwork(input_dim, 256, len(ACTIONS)).to(CFG.DEVICE)
    target_net = QNetwork(input_dim, 256, len(ACTIONS)).to(CFG.DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    optimizer = optim.Adam(policy_net.parameters(), lr=CFG.LR_DQN)
    scaler = amp.GradScaler()
    buffer = ReplayBuffer(CFG.BUFFER_CAPACITY)
    step_count = 0
    best_reward = -float("inf")   # track best episode reward

    rewards    = []  # total reward per episode
    eps        = CFG.EPS_INIT
    eps_list    = []
    losses_list = []
    waits_list  = []
    q_list      = []

    with tqdm(range(NUM_EPISODES), desc="Training Episodes") as bar:
        for ep in bar:
            with suppress_output():
                step_count, ep_reward, ep_loss, ep_wait, ep_q = run_episode(
                    policy_net, target_net, buffer, optimizer,
                    ep, rewards, eps, step_count, scaler,
                    num_envs=CFG.NUM_ENVS,
                )

            # store metrics (buffered in memory, written in chunks)
            metrics_rows.append([
                ep + 1,
                f"{ep_reward:.4f}",
                f"{ep_loss:.6f}",
                f"{ep_wait:.2f}",
                f"{ep_q:.3f}",
                f"{eps:.4f}",
                num_edges,
                num_lanes,
                f"{total_lane_length:.2f}"
            ])
            # Write to disk every 20 episodes to avoid excessive file I/O
            if (ep + 1) % 20 == 0:  # log/write interval changed from 50 to 20
                csv_writer.writerows(metrics_rows)
                metrics_rows.clear()
            # append diagnostic metrics
            losses_list.append(ep_loss)
            waits_list.append(ep_wait)
            q_list.append(ep_q)
            eps_list.append(eps)
            # decay ε after each episode to allow exploitation
            eps = max(CFG.EPS_MIN, eps * CFG.EPS_DECAY)

            # --- check‑pointing -----------------------------------------------
            if ep_reward > best_reward:
                best_reward = ep_reward
                torch.save(policy_net.state_dict(), best_ckpt_path)

            if (ep + 1) % 100 == 0 and len(rewards) >= 100:
                avg = sum(rewards[-100:]) / 100
                logging.info(f"[Ep {ep+1}] avg_reward(100)={avg:.1f}, eps={eps:.3f}")

            bar.set_postfix(
                R=f"{ep_reward:.2f}",
                L=f"{ep_loss:.4f}",
                W=f"{ep_wait:.1f}",
                Q=f"{ep_q:.2f}",
                ε=f"{eps:.3f}"
            )
    # write any remaining buffered rows
    if metrics_rows:
        csv_writer.writerows(metrics_rows)
    csv_file.close()

    # --- save final checkpoint ----------------------------------------------
    torch.save(policy_net.state_dict(), final_ckpt_path)
    print(f"[Checkpoint] Best model → {best_ckpt_path.as_posix()}")
    print(f"[Checkpoint] Final model → {final_ckpt_path.as_posix()}")
    
    """
    Additional diagnostic plots
    """
    import matplotlib.pyplot as plt
    #1 plot mean loss per episode
    plt.figure()
    plt.plot(range(1, NUM_EPISODES+1), losses_list)
    plt.xlabel("Episode"); plt.ylabel("Mean Loss"); plt.title("Loss per Episode"); plt.grid(True)
    plt.savefig(log_dir/"loss_plot.png"); plt.close()
    #2 plot mean wait per episode
    plt.figure()
    plt.plot(range(1, NUM_EPISODES+1), waits_list)
    plt.xlabel("Episode"); plt.ylabel("Mean Waiting Time"); plt.title("Wait per Episode"); plt.grid(True)
    plt.savefig(log_dir/"wait_plot.png"); plt.close()
    #3 plot mean Q value per episode
    plt.figure()
    plt.plot(range(1, NUM_EPISODES+1), q_list)
    plt.xlabel("Episode"); plt.ylabel("Mean Q Value"); plt.title("Q Value per Episode"); plt.grid(True)
    plt.savefig(log_dir/"q_plot.png"); plt.close()
    #4 plot epsilon decay
    plt.figure()
    plt.plot(range(1, NUM_EPISODES+1), eps_list)
    plt.xlabel("Episode"); plt.ylabel("Epsilon"); plt.title("Epsilon Decay per Episode"); plt.grid(True)
    plt.savefig(log_dir/"eps_plot.png"); plt.close()
    #5 plot reward
    plt.plot(range(1, NUM_EPISODES + 1), rewards, marker="o")
    plt.xlabel("Episode"); plt.ylabel("Total Reward"); plt.title("Reward per Episode"); plt.grid(True)
    plt.savefig(log_dir/"reward_plot.png"); plt.close()
    print(f"Training complete — 5 artifacts saved to {log_dir}/.")


__all__ = [
    "set_full_red",
    "clear_full_red",
    "handle_emergency_blockage",
    "MultiprocessingTrafficEnv",
]

if __name__ == "__main__":
    main()
    