"""
This file is used to optimize ESS usage for export energy minimization.
Given energy rates in cyprus, this is the equivalent to price minimization. 
"""

import scipy.optimize as spo
import numpy as np
from ..models import ESS
from forecasting.models import PVPanel
import logging
log = logging.getLogger(__name__)


class MinEnergyExport:
    def __init__(self, ess: ESS, pv: PVPanel):
        self.ess = ess

    # Default to UCY Microgrid ess:
    def __init__(self):
        self.ess = ESS.objects.get(name="future-ucy-battery")

    # returns the objective function; x is power out of ESS (positive for discharge, negative for charge)
    def _get_objective(self, pred_net_load: np.array):
        # Define the objective function
        def objective(x):
            grid_net_load = np.zeros(pred_net_load.shape[0])

            for t in range(pred_net_load.shape[0]):
                grid_net_load[t] = max(
                    0,
                    pred_net_load[t]
                    - (
                        (x[t] * self.ess.discharge_efficiency)
                        if x[t] > 0
                        else x[t] * self.ess.charge_efficiency
                    ),
                )

            return np.sum(grid_net_load)

        return objective

    # returns constraint list; x is power out of ESS (positive for discharge, negative for charge)
    def _get_constraints(self, pred_net_load: np.array):
        # Define the Soc Constraint
        def soc_constraint(x):
            soc = np.zeros(pred_net_load.shape[0] + 1)  # in MWh
            soc[0] = 0.5

            for t in range(pred_net_load.shape[0]):
                soc[t + 1] = (
                    soc[t]
                    - (
                        (x[t] * self.ess.discharge_efficiency / self.ess.capacity)
                        if x[t] > 0
                        else x[t] * self.ess.charge_efficiency / self.ess.capacity
                    )
                    - self.ess.self_discharge * soc[t]
                )

            return self.ess.pref_max_soc - soc, soc - self.ess.pref_min_soc

        # Define battery max charge constraint
        def charge_constraint(x):
            return self.ess.max_charge + x, self.ess.max_discharge - x
        
        return [
            {"type": "ineq", "fun": lambda x: soc_constraint(x)[0]},
            {"type": "ineq", "fun": lambda x: soc_constraint(x)[1]},
            {"type": "ineq", "fun": lambda x: charge_constraint(x)[0]},
            {"type": "ineq", "fun": lambda x: charge_constraint(x)[1]}
        ]

    # Perform the optimization
    def optimize(self, pred_net_load: np.array, method: str = "SLSQP"):
        x0 = np.zeros(pred_net_load.shape[0])
        
        result = spo.minimize(
            self._get_objective(pred_net_load),
            x0,
            method=method,
            constraints=self._get_constraints(pred_net_load),
            options={'maxiter': 4000, 'disp': True}
        )

        if result.success:
            # Calculate the state of charge for each time step
            soc = np.zeros(pred_net_load.shape[0])
            for i in range(pred_net_load.shape[0]):
                soc[i] = (
                    (0.5 if i == 0 else soc[i - 1])
                    - (
                        (result.x[i] * self.ess.discharge_efficiency / self.ess.capacity)
                        if result.x[i] > 0
                        else result.x[i] * self.ess.charge_efficiency / self.ess.capacity
                    )
                    - self.ess.self_discharge * (0.5 if i == 0 else soc[i - 1])
                )

            return result.x, soc
        else: 
            return False
