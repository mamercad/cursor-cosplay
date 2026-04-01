#!/usr/bin/env python3
"""Find all prime numbers from 2 through 10000 and write them to a file (one per line)."""

from __future__ import annotations

import argparse
from pathlib import Path


def primes_up_to(n: int) -> list[int]:
    """Return primes p with 2 <= p <= n using the sieve of Eratosthenes."""
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    limit = int(n**0.5) + 1
    for i in range(2, limit):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("primes_10000.txt"),
        help="output file path (default: primes_10000.txt in the current directory)",
    )
    parser.add_argument(
        "-n",
        "--max",
        type=int,
        default=10000,
        help="upper bound inclusive (default: 10000)",
    )
    args = parser.parse_args()

    primes = primes_up_to(args.max)
    args.output.write_text("\n".join(str(p) for p in primes) + "\n", encoding="utf-8")
    print(f"Wrote {len(primes)} primes (2..{args.max}) to {args.output.resolve()}")


if __name__ == "__main__":
    main()
