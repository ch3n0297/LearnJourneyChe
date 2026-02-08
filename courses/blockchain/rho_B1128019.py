#!/usr/bin/env python3
"""
Pollard's Rho - Simplified CPU version for smaller problems
"""

import time
import sys

# Problem parameters (group 0)
P = 11
G = 2
H = 9
ORDER = 10

print("=" * 70)
print("Pollard's Rho DLP Solver - CPU (Simplified)")
print("=" * 70)
print(f"\nParameters (Group 0):")
print(f"  p = {P} ({P.bit_length()} bits)")
print(f"  g = {G}")
print(f"  h = {H}")
print(f"  order = {ORDER} ({ORDER.bit_length()} bits)")

# Validation
print(f"\n[Validation]")
g_n = pow(G, ORDER, P)
h_n = pow(H, ORDER, P)
print(f"  g^order mod p = {g_n} {'✓' if g_n == 1 else '✗'}")
print(f"  h^order mod p = {h_n} {'✓' if h_n == 1 else '✗'}")

if g_n != 1 or h_n != 1:
    print("\nERROR: Validation failed!")
    sys.exit(1)

# Precompute r-adding table
N_PARTITIONS = 64
print(f"\n[Precomputing {N_PARTITIONS} multipliers...]")

import random
random.seed(42)

multipliers = []
for i in range(N_PARTITIONS):
    delta_a = random.randint(1, ORDER - 1)
    delta_b = random.randint(1, ORDER - 1)
    factor = (pow(G, delta_a, P) * pow(H, delta_b, P)) % P
    multipliers.append({
        'factor': factor,
        'delta_a': delta_a,
        'delta_b': delta_b
    })

print(f"  Multipliers precomputed")

# Distinguished points (use top 2 bits = 0, i.e., 1 in 4)
DIST_BITS = 2
DP_THRESHOLD = 1 << (P.bit_length() - DIST_BITS)

print(f"\n[Configuration]")
print(f"  Distinguished bits: {DIST_BITS}")
print(f"  Expected DP rate: ~1/{1 << DIST_BITS}")
print(f"  Expected iterations to collision: ~{int(ORDER**0.5):,}")

# Run Pollard's rho
print(f"\n[Running Pollard's rho...]")
print(f"{'Iterations':<15} {'DPs':<10} {'Time':<10} {'Rate (K/s)':<12}")
print("-" * 70)

dp_table = {}
total_iters = 0
start_time = time.time()
found = False

try:
    while total_iters < 5_000_000_000:  # Max 5B iterations
        # Random starting point
        a = random.randint(1, ORDER - 1)
        b = random.randint(1, ORDER - 1)
        x = (pow(G, a, P) * pow(H, b, P)) % P

        # Random walk until distinguished point
        walk_len = 0
        max_walk = 1_000_000  # Prevent infinite loops

        while walk_len < max_walk:
            # Partition function
            partition = x % N_PARTITIONS

            # Update x, a, b
            x = (x * multipliers[partition]['factor']) % P
            a = (a + multipliers[partition]['delta_a']) % ORDER
            b = (b + multipliers[partition]['delta_b']) % ORDER

            walk_len += 1
            total_iters += 1

            # Check if distinguished
            if x < DP_THRESHOLD:
                # Found DP
                if x in dp_table:
                    # Collision!
                    prev_a, prev_b = dp_table[x]

                    if prev_a != a or prev_b != b:
                        # Solve: (prev_a - a) = x_solution * (b - prev_b) mod order
                        numerator = (prev_a - a) % ORDER
                        denominator = (b - prev_b) % ORDER

                        if denominator != 0:
                            try:
                                denom_inv = pow(denominator, -1, ORDER)
                                x_solution = (numerator * denom_inv) % ORDER

                                # Verify
                                if pow(G, x_solution, P) == H:
                                    elapsed = time.time() - start_time
                                    print(f"\n{'='*70}")
                                    print(f"[SOLUTION FOUND!]")
                                    print(f"  Time: {elapsed:.1f}s")
                                    print(f"  Iterations: {total_iters:,}")
                                    print(f"  DPs collected: {len(dp_table):,}")
                                    print(f"\n{{")
                                    print(f'  "grp": 0,')
                                    print(f'  "id": "B1128019",')
                                    print(f'  "x": "{x_solution}",')
                                    print(f'  "verified": true')
                                    print(f"}}")
                                    print(f"{'='*70}")
                                    found = True
                                    break
                            except:
                                pass
                else:
                    dp_table[x] = (a, b)

                break  # Start new walk

        if found:
            break

        # Progress update
        if total_iters % 100000 == 0:
            elapsed = time.time() - start_time
            rate = total_iters / elapsed / 1000 if elapsed > 0 else 0
            print(f"{total_iters:<15,} {len(dp_table):<10,} {elapsed:9.1f}s {rate:11.1f}", end='\r')

except KeyboardInterrupt:
    print(f"\n\n[Interrupted by user]")

elapsed = time.time() - start_time
print(f"\n\n{'='*70}")
print(f"[Summary]")
print(f"  Total time: {elapsed:.1f}s")
print(f"  Total iterations: {total_iters:,}")
print(f"  Distinguished points: {len(dp_table):,}")
print(f"  Average rate: {total_iters / elapsed / 1000:.1f} K iter/s")
print(f"  Result: {'FOUND ✓' if found else 'Not found'}")
print(f"{'='*70}")
