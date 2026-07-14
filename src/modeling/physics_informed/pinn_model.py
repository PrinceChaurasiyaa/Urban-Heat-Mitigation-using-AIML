"""M4: Physics-informed neural network. Implements FR-4.2, FR-4.5.

Combines a standard prediction loss (MSE against observed LST) with a
regularization term penalizing violation of the surface energy balance
(Rn = H + LE + G), as described in SRS Section 8.1.
"""

import torch
import torch.nn as nn


class PhysicsInformedLSTModel(nn.Module):
    def __init__(self, n_features, hidden_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x):
        return self.net(x)


def physics_informed_loss(y_pred, y_true, energy_balance_residual, loss_weight=0.3):
    """
    Composite loss: data-fit MSE + weighted energy-balance residual penalty.
    `energy_balance_residual` should be precomputed per-sample (Rn - (H+LE+G)).
    """
    mse = nn.functional.mse_loss(y_pred, y_true)
    physics_penalty = torch.mean(energy_balance_residual ** 2)
    return mse + loss_weight * physics_penalty
