"""M6: Optimization objective and constraint definitions. Implements FR-5.6."""


def hotspot_weighted_reduction(baseline_lst, scenario_lst, hotspot_weight_mask):
    """
    Objective function: weighted mean temperature reduction, weighted more
    heavily toward existing severe hotspots than uniformly across the AOI.
    """
    reduction = baseline_lst - scenario_lst
    return (reduction * hotspot_weight_mask).sum() / hotspot_weight_mask.sum()


def budget_constraint(intervention_plan, cost_table, max_budget):
    total_cost = sum(cost_table[i["type"]] * i["area_m2"] for i in intervention_plan)
    return total_cost <= max_budget
