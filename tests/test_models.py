"""Mathematical invariants and failure-sensitive image-pipeline checks."""
import unittest
import numpy as np
from src import phase_ring as ring
from src.plp import prototype,prototype_v2,wiener_plane,latch

class PhaseRingTests(unittest.TestCase):
    def test_requested_vectors(self):
        for a,b,n,expected in [(1023,1,1024,0),(750,400,1024,126),(1500,800,2048,252)]:
            self.assertEqual(ring.paper_step(a,b,n)[0],expected)

    def test_exhaustive_addition(self):
        for n in [1024,2048]:
            a=np.arange(n,dtype=np.uint16)[:,None]
            b=np.arange(n,dtype=np.uint16)[None,:]
            np.testing.assert_array_equal(ring.add(a,b,n),(a.astype(np.uint32)+b.astype(np.uint32))%n)

    def test_floor_and_wrap(self):
        for n in [1024,2048]:
            np.testing.assert_array_equal(ring.quantize(np.array([0,np.pi,-np.pi,-1e-8,2*np.pi]),n),[0,n//2,n//2,n-1,0])

    def test_all_lut_addresses(self):
        for n in [1024,2048]:
            lut=ring.make_lut(n);t=np.arange(n)*2*np.pi/n
            np.testing.assert_array_equal(lut[:,1],np.int16(np.sin(np.linspace(0,2*np.pi,n,endpoint=False))*32767))
            z=ring.decode(np.arange(n),lut)
            self.assertLess(float(np.max(np.abs(z-np.exp(1j*t)))),np.sqrt(2)/32767+2e-7)

    def test_quantization_bound(self):
        rng=np.random.default_rng(123);a,b=rng.uniform(-np.pi,np.pi,(2,20000))
        for n in [1024,2048]:
            z=ring.end_to_end(a,b,n,ring.make_lut(n))
            err=np.abs(np.angle(z*np.exp(-1j*(a+b))))
            self.assertLess(float(err.max()),4*np.pi/n+5e-5)

    def test_invalid_modulus(self):
        with self.assertRaises(ValueError):ring.add(1,2,360)

class PrototypeTests(unittest.TestCase):
    def test_legacy_plane_is_preserved(self):
        x=np.random.default_rng(72).random((32,32),dtype=np.float32)
        np.testing.assert_array_equal(wiener_plane(x,0.06),prototype(x,0.06,True)[0])

    def test_intensity_latch_error_bound(self):
        x=np.linspace(0,1,10001,dtype=np.float32)
        self.assertLessEqual(float(np.max(np.abs(latch(x)-x))),1/2046+1e-7)

    def test_v2_reduces_flat_noise_and_is_deterministic(self):
        x=np.clip(0.4+np.random.default_rng(8).normal(0,0.06,(48,48)),0,1).astype(np.float32)
        result=prototype_v2(x,0.06)
        self.assertLess(float(np.mean((result-0.4)**2)),float(np.mean((x-0.4)**2)))
        self.assertTrue(np.isfinite(result).all())
        np.testing.assert_array_equal(result,prototype_v2(x,0.06))

    def test_constant_and_bounds(self):
        x=np.full((32,32),0.5,np.float32);y=prototype(x,0.06)
        self.assertEqual(y.shape,x.shape)
        self.assertLess(float(np.max(np.abs(y-x))),1/1023)
        self.assertTrue(np.isfinite(y).all())
        self.assertTrue(((y>=0)&(y<=1)).all())

    def test_real_denoising_and_repeatability(self):
        rng=np.random.default_rng(1);x=np.clip(0.5+rng.normal(0,0.06,(64,64)),0,1).astype(np.float32)
        y=prototype(x,0.06)
        self.assertLess(float(np.mean((y-0.5)**2)),float(np.mean((x-0.5)**2)))
        np.testing.assert_array_equal(y,prototype(x,0.06))
        self.assertEqual(len(prototype(x,0.06,True)),3)

if __name__=='__main__':unittest.main()
