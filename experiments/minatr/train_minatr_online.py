import argparse

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

import afbc
import gym
from minatar_utils import MinAtarEnv, MinAtarEncoder


def train_minatar_online(args):
    train_env = MinAtarEnv(args.game)
    test_env = MinAtarEnv(args.game)

    # create agent
    agent = afbc.AFBCAgent(
        act_space_size=6,
        encoder=MinAtarEncoder(channels=train_env.num_channels),
        actor_network_cls=afbc.nets.mlps.DiscreteActor,
        critic_network_cls=afbc.nets.mlps.DiscreteCritic,
        hidden_size=256,
        discrete=True,
    )

    buffer = afbc.replay.PrioritizedReplayBuffer(size=1_000_000)

    # run training
    afbc.afbc(
        agent=agent,
        train_env=train_env,
        test_env=test_env,
        buffer=buffer,
        verbosity=1,
        name=args.name,
        use_pg_update_online=True,
        use_bc_update_online=False,
        num_steps_offline=0,
        num_steps_online=5_000_000,
        random_warmup_steps=10_000,
        max_episode_steps=100_000,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=str, default="breakout")
    parser.add_argument("--name", type=str, default="afbc_minatar_online")
    args = parser.parse_args()
    train_minatar_online(args)