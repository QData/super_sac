from torch import nn


def weight_init(m):
    if isinstance(m, nn.Linear):
        nn.init.orthogonal_(m.weight.data)
        m.bias.data.fill_(0.0)
    elif isinstance(m, nn.Conv2d) or isinstance(m, nn.ConvTranspose2d):
        # delta-orthogonal init from https://arxiv.org/pdf/1806.05393.pdf
        assert m.weight.size(2) == m.weight.size(3)
        m.weight.data.fill_(0.0)
        m.bias.data.fill_(0.0)
        mid = m.weight.size(2) // 2
        gain = nn.init.calculate_gain("relu")
        nn.init.orthogonal_(m.weight.data[:, :, mid, mid], gain)


from abc import ABC, abstractmethod


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.have_at_least_one_param = nn.Linear(1, 1)

    def forward_rolling(self, obs):
        return self.forward(obs)

    def reset_rolling(self):
        pass

    @property
    @abstractmethod
    def embedding_dim(self):
        raise NotImplementedError


from . import mlps, cnns, distributions
