import math

import torch
import torch.distributions as pyd
import torch.nn.functional as F
import numpy as np


def create_tanh_normal(vec, log_std_low, log_std_high):
    mu, log_std = vec.chunk(2, dim=-1)
    log_std = torch.tanh(log_std)
    log_std = log_std_low + 0.5 * (log_std_high - log_std_low) * (log_std + 1)
    std = log_std.exp()
    dist = SquashedNormal(mu, std)
    return dist


def create_beta(vec):
    vec = 1.0 + F.softplus(vec)
    alpha, beta = vec.chunk(2, dim=-1)
    dist = BetaDist(alpha, beta)
    return dist


class BetaDist(pyd.transformed_distribution.TransformedDistribution):
    class _BetaDistTransform(pyd.transforms.Transform):
        domain = pyd.constraints.real
        codomain = pyd.constraints.interval(-1.0, 1.0)

        def __init__(self, cache_size=1):
            super().__init__(cache_size=cache_size)

        def __eq__(self, other):
            return isinstance(other, _BetaDistTransform)

        def _inverse(self, y):
            return (y.clamp(-0.99, 0.99) + 1.0) / 2.0

        def _call(self, x):
            return (2.0 * x) - 1.0

        def log_abs_det_jacobian(self, x, y):
            # return log det jacobian |dy/dx| given input and output
            return torch.Tensor([math.log(2.0)]).to(x.device)

    def __init__(self, alpha, beta):
        self.base_dist = pyd.beta.Beta(alpha, beta)
        transforms = [self._BetaDistTransform()]
        super().__init__(self.base_dist, transforms)

    @property
    def mean(self):
        mu = self.base_dist.mean
        for tr in self.transforms:
            mu = tr(mu)
        return mu


"""
Credit for actor distribution code: https://github.com/denisyarats/pytorch_sac/blob/master/agent/actor.py
"""


class TanhTransform(pyd.transforms.Transform):
    domain = pyd.constraints.real
    codomain = pyd.constraints.interval(-1.0, 1.0)
    bijective = True
    sign = +1

    def __init__(self, cache_size=1):
        super().__init__(cache_size=cache_size)

    @staticmethod
    def atanh(x):
        return 0.5 * (x.log1p() - (-x).log1p())

    def __eq__(self, other):
        return isinstance(other, TanhTransform)

    def _call(self, x):
        return x.tanh()

    def _inverse(self, y):
        return self.atanh(y.clamp(-0.99, 0.99))

    def log_abs_det_jacobian(self, x, y):
        return 2.0 * (math.log(2.0) - x - F.softplus(-2.0 * x))


class SquashedNormal(pyd.transformed_distribution.TransformedDistribution):
    def __init__(self, loc, scale):
        self.loc = loc
        self.scale = scale

        self.base_dist = pyd.Normal(loc, scale)
        transforms = [TanhTransform()]
        super().__init__(self.base_dist, transforms)

    @property
    def mean(self):
        mu = self.loc
        for tr in self.transforms:
            mu = tr(mu)
        return mu


class ContinuousDeterministic(pyd.Normal):
    def __init__(self, deterministic_actor_output):
        super().__init__(
            loc=deterministic_actor_output, scale=1e-4, validate_args=False
        )

    def sample(self):
        return self.loc
