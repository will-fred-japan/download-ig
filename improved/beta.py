import math
from typing import Optional

import numpy as np

# Internal state for streak control
_last_val = None
_streak_len = 0


def reset_skew_state() -> None:
    """Reset the state used to avoid value streaking."""
    global _last_val, _streak_len
    _last_val = None
    _streak_len = 0


def generate_skewed_random(
    base=5.0,
    skew=-0.7,
    max_value=20,
    offset=1,
    as_int=False,
    max_streak=2,
    rng: Optional[np.random.Generator] = None,
):
    """
    Generate a value from a skewed Beta distribution while reducing repetitive streaks.

    Parameters:
        base: controls the overall distribution shape
        skew: negative skew makes lower values more likely; positive makes higher values more likely
        max_value: upper bound for the randomized quantity
        offset: value added after sampling
        as_int: if True, sample from a discrete integer grid
        max_streak: longest allowed repeated value before resampling
        rng: optional numpy Generator for reproducible testing
    """
    global _last_val, _streak_len

    if max_value <= 0:
        raise ValueError("max_value must be > 0")
    if base <= 0:
        raise ValueError("base must be > 0")

    rand = rng if rng is not None else np.random
    alpha = max(base + skew * base, 0.05)
    beta_ = max(base - skew * base, 0.05)

    while True:
        if as_int:
            xs = np.arange(max_value + 1, dtype=np.float64)
            grid = (xs + 0.5) / (max_value + 1)
            probs = (grid ** (alpha - 1.0)) * ((1.0 - grid) ** (beta_ - 1.0))
            probs = np.nan_to_num(probs, nan=0.0, posinf=0.0, neginf=0.0)
            if not np.any(probs):
                probs = np.ones_like(probs) / len(probs)
            else:
                probs = probs / probs.sum()
            val = int(rand.choice(xs, p=probs) + offset)
        else:
            val = float(rand.beta(alpha, beta_) * max_value + offset)

        if _last_val is not None and val == _last_val:
            if _streak_len < max_streak:
                _streak_len += 1
                break
            continue

        _last_val = val
        _streak_len = 1
        break

    return val


if __name__ == "__main__":
    reset_skew_state()
    values = [generate_skewed_random(base=5, skew=-0.75, max_value=30, offset=2, as_int=False) for _ in range(30)]
    print(values)
