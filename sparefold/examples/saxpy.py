"""SAXPY, two ways. The kernel checker compares them. No GPU required."""


def saxpy(a: float, x: list[float], y: list[float]) -> list[float]:
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    return [a * x[i] + y[i] for i in range(len(x))]


def saxpy_indexed(a: float, x: list[float], y: list[float]) -> list[float]:
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    out = []
    for index, xi in enumerate(x):
        out.append((a * xi) + y[index])
    return out
