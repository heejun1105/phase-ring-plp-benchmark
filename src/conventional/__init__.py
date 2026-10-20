"""Vectorized complex64 reference operations."""
import numpy as np

def encode_pair(a, b):
    """Encode identical input angles as unit-magnitude complex64 operands."""
    return np.exp(1j * a).astype(np.complex64), np.exp(1j * b).astype(np.complex64)

def multiply(a, b):
    """One unit-phasor product per element; this is not a general MAC."""
    return np.multiply(a, b)

def end_to_end(a, b):
    x, y = encode_pair(a, b)
    return multiply(x, y)
