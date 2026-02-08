import multiprocessing as mp
from typing import List, Tuple


def _worker(conn):
    """Process target: run a TrafficEnv instance and respond to commands."""
    from train import TrafficEnv  # imported lazily to avoid circular import

    env = TrafficEnv()
    while True:
        cmd = conn.recv()
        if cmd == "reset":
            state = env.reset()
            conn.send((state, env.state_wait))
        elif cmd == "close":
            env.close()
            conn.close()
            break
        else:
            action = cmd
            next_state, reward, done = env.step(action)
            conn.send((next_state, reward, done, env.state_wait))
            if done:
                # episode done; caller may reset or close
                pass


class MultiprocessingTrafficEnv:
    """Launch multiple ``TrafficEnv`` workers and step them in parallel."""

    def __init__(self, num_envs: int):
        self.num_envs = num_envs
        self.conns: List[mp.connection.Connection] = []
        self.ps: List[mp.Process] = []
        for _ in range(num_envs):
            parent_conn, child_conn = mp.Pipe()
            p = mp.Process(target=_worker, args=(child_conn,))
            p.daemon = True
            p.start()
            child_conn.close()
            self.conns.append(parent_conn)
            self.ps.append(p)
        # initialize all envs
        for c in self.conns:
            c.send("reset")
        self.states = [c.recv()[0] for c in self.conns]
        self.waits = [0.0 for _ in range(num_envs)]

    def step(self, actions: List[int]) -> Tuple[List[Tuple], List[float], List[bool], List[float]]:
        for c, a in zip(self.conns, actions):
            c.send(a)
        results = [c.recv() for c in self.conns]
        next_states, rewards, dones, waits = [], [], [], []
        for res in results:
            ns, r, d, w = res
            next_states.append(ns)
            rewards.append(r)
            dones.append(d)
            waits.append(w)
        self.states = next_states
        self.waits = waits
        return next_states, rewards, dones, waits

    def close(self) -> None:
        for c in self.conns:
            c.send("close")
        for p in self.ps:
            p.join()
