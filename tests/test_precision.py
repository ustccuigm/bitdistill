"""Numerical contracts shared by the learner and packed runtime."""
import unittest
import torch
from steerdistill.quantization.precision import pack_codes, unpack_codes, quantize_activation, validate_precision
from steerdistill.quantization.qlinear import QLinear
from steerdistill.training.convert_hf_to_awq_runtime import quantized_linear_tensors
from steerdistill.runtime_validation import unpack_awq


class PrecisionTest(unittest.TestCase):
    def test_packing_covers_all_codes_and_signed_words(self):
        for bits in (2, 4):
            x = torch.arange(512).reshape(4, 128) % (1 << bits)
            packed = pack_codes(x, bits)
            self.assertTrue(torch.equal(unpack_codes(packed, bits), x))
            self.assertEqual(packed.numel() * 32, x.numel() * bits)

    def test_export_matches_learner_and_gradients(self):
        torch.manual_seed(9)
        for bits, activation_bits in ((2, 16), (4, 8), (4, 16)):
            with self.subTest(bits=bits, activation_bits=activation_bits):
                layer = QLinear(128, 64, bias=False, compute_dtype=torch.bfloat16,
                                quant_type=f'int{bits}-asym', w_bit=bits,
                                activation_bits=activation_bits).to(torch.bfloat16)
                x = torch.randn(3, 128, dtype=torch.bfloat16, requires_grad=True)
                actual = layer(x)
                packed = quantized_linear_tensors(layer, bits, 64, activation_bits)
                unpack = unpack_awq if (bits, activation_bits) == (4, 16) else unpack_codes
                codes = unpack(packed['qweight'], bits)
                zeros = unpack(packed['qzeros'], bits).repeat_interleave(64, 0)
                scales = packed['scales'].float().repeat_interleave(64, 0)
                weights = ((codes - zeros) * scales).to(x.dtype)
                expected = quantize_activation(x.detach(), activation_bits) @ weights
                torch.testing.assert_close(actual, expected, rtol=0, atol=0)
                actual.float().square().mean().backward()
                for grad in (layer.weight.grad, x.grad):
                    self.assertTrue(torch.isfinite(grad).all())
                    self.assertGreater(grad.abs().sum().item(), 0)

    def test_activation_zero_scale_and_token_independence(self):
        x = torch.tensor([[0.,0.,0.],[1.,.123, -.5],[100.,12.3,-50.]])
        q = quantize_activation(x, 8)
        self.assertTrue(torch.isfinite(q).all())
        self.assertTrue(torch.equal(q[0], x[0]))
        torch.testing.assert_close(q[1] * 100, q[2])
        self.assertFalse(torch.equal(q, x))
        x.requires_grad_();quantize_activation(x, 8, ste=True).sum().backward()
        self.assertTrue(torch.equal(x.grad, torch.ones_like(x)))

    def test_reject_unsupported_precision(self):
        with self.assertRaises(ValueError): validate_precision(2, 8)
        with self.assertRaises(ValueError): pack_codes(torch.zeros(3, 17), 2)


if __name__ == '__main__': unittest.main()
