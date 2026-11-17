"""A deterministic corridor. The gym checker has something real to accept."""


class Discrete:
    def __init__(self, n: int) -> None:
        if n < 1:
            raise ValueError("n must be positive")
        self.n = n

    def contains(self, value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and 0 <= value < self.n


class Corridor:
    """Positions 0..length-1. Right moves toward the goal. Reward 1 on entering it."""

    def __init__(self, length: int = 5) -> None:
        if length < 2:
            raise ValueError("length must be at least 2")
        self.length = length
        self.observation_space = Discrete(length)
        self.action_space = Discrete(2)
        self.pos = 0
        self._done = False

    def reset(self, seed: int | None = None):
        self.pos = 0
        self._done = False
        return self.pos, {"seed": seed}

    def step(self, action: int):
        if self._done:
            raise RuntimeError("episode is done")
        if not self.action_space.contains(action):
            raise ValueError(f"invalid action {action}")
        if action == 1 and self.pos < self.length - 1:
            self.pos += 1
        elif action == 0 and self.pos > 0:
            self.pos -= 1
        terminated = self.pos == self.length - 1
        self._done = terminated
        reward = 1.0 if terminated else 0.0
        return self.pos, reward, terminated, False, {}
