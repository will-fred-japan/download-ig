import numpy as np
from collections import Counter

# --- internal state for streak control ---
_last_val = None
_streak_len = 0

WAIT_TIME_MAX = 50                  # Max wait time between actions

def generate_skewed_random(base=5.0, skew=-0.7, max_value=20, offset=1,
                           as_int=False, max_streak=2):
    """
    Generate a random value using a skewed Beta distribution,
    with baked-in streak control.
    """
    global _last_val, _streak_len

    # map skew into alpha/beta
    alpha = base + skew * base
    beta_ = base - skew * base

    # keep them > 0
    alpha = max(alpha, 0.1)
    beta_ = max(beta_, 0.1)

    while True:
        if as_int:
            xs = np.arange(max_value + 1)
            grid = (xs + 0.5) / (max_value + 1)

            probs = (grid ** (alpha - 1)) * ((1 - grid) ** (beta_ - 1))
            probs = np.nan_to_num(probs, nan=0.0, posinf=0.0, neginf=0.0)

            if probs.sum() == 0:
                probs = np.ones_like(probs) / len(probs)
            else:
                probs /= probs.sum()

            val = int(np.random.choice(xs, p=probs) + offset)
        else:
            val = np.random.beta(alpha, beta_) * max_value + offset

        # streak control
        if val == _last_val:
            if _streak_len < max_streak:
                _streak_len += 1
                break
            else:
                continue  # resample until different
        else:
            _last_val = val
            _streak_len = 1
            break

    return val


# --- Example usage for tuning ---

if __name__ == "__main__":
    WAIT_TIME_MAX = 30.0  # define your max value

    results = [
        # generate_skewed_random(base=5, skew=-0.75, max_value=WAIT_TIME_MAX, offset=2, as_int=False)
        generate_skewed_random(base=5, skew=-0.75, max_value=WAIT_TIME_MAX, offset=2, as_int=False)
        for _ in range(35)
    ]

    # round to 3 decimal places
    rounded_results = [round(r, 3) for r in results]

    # frequency count
    freq = Counter(rounded_results)

    # print raw results
    print("\nResults (3 dp):", rounded_results)

    # print summary
    print("\nSummary (value → frequency):")
    for value in sorted(freq):
        print(f"{value:.3f}: {freq[value]}")
    print()
