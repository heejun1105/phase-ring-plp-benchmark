"""Paper VIII Eq. (1)-(4) and Listing 2, with reusable LUT construction."""
import numpy as np

def validate_modulus(n):
    if n not in (1024, 2048):
        raise ValueError('Supported moduli are 1024 and 2048.')

def quantize(angle, n):
    """Floor angle*N/(2*pi), then wrap; do not round to nearest."""
    validate_modulus(n)
    return np.remainder(np.floor(np.asarray(angle) * (n / (2*np.pi))), n).astype(np.uint16)

def add(a, b, n):
    """Software mask emulates 10/11-bit RTL truncation, not uint16 overflow."""
    validate_modulus(n)
    return np.bitwise_and(np.add(a, b, dtype=np.uint16), np.uint16(n-1))

def make_lut(n):
    """Paper-exact sine Q15 truncation plus cosine for a fair complex output."""
    validate_modulus(n)
    t = np.arange(n, dtype=np.float64) * (2*np.pi/n)
    return np.stack([np.cos(t)*32767, np.sin(t)*32767], axis=-1).astype(np.int16)

def decode(index, lut):
    """Restore both Q15 channels to complex64; costs are benchmarked."""
    values = lut[index].astype(np.float32) / np.float32(32767)
    return (values[..., 0] + np.complex64(1j)*values[..., 1]).astype(np.complex64)

def encoded_complex(a, b, n, lut):
    return decode(add(a, b, n), lut)

def end_to_end(a, b, n, lut):
    return encoded_complex(quantize(a, n), quantize(b, n), n, lut)

def paper_step(a, b, n=1024):
    """Reproduce Listing 2 output using a scalar sine LUT entry."""
    total = (int(a) + int(b)) & (n-1)
    return total, int(make_lut(n)[total, 1])
