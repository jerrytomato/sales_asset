from dataclasses import dataclass

import numpy as np


@dataclass
class SimulationParams:
    total_opportunities: float
    ota_share: float
    direct_completion_mean: float
    ota_completion_mean: float
    revenue_per_booking_mean: float
    commission_rate: float
    sigma: float
    capacity: float
    iterations: int
    target_revenue: float


def _beta_samples(mean: float, strength: float, size: int) -> np.ndarray:
    mean = np.clip(mean, 1e-4, 1 - 1e-4)
    alpha = mean * strength
    beta = (1 - mean) * strength
    return np.random.beta(alpha, beta, size=size)


def _lognormal_samples(mean: float, sigma: float, size: int) -> np.ndarray:
    sigma = max(1e-3, sigma)
    mu = np.log(mean) - 0.5 * sigma * sigma
    return np.random.lognormal(mean=mu, sigma=sigma, size=size)


def _capacity_clip(
    direct_bookings: np.ndarray, ota_bookings: np.ndarray, capacity: float
):
    total = direct_bookings + ota_bookings
    cap = np.minimum(total, capacity)
    with np.errstate(divide="ignore", invalid="ignore"):
        direct_ratio = np.where(total > 0, direct_bookings / total, 0.0)
    ota_ratio = 1 - direct_ratio
    direct_capped = cap * direct_ratio
    ota_capped = cap * ota_ratio
    return direct_capped, ota_capped, total > capacity


def simulate_revenue(params: SimulationParams):
    n = params.iterations
    direct_share = 1 - params.ota_share

    direct_opps = params.total_opportunities * direct_share
    ota_opps = params.total_opportunities * params.ota_share

    direct_completion = _beta_samples(
        params.direct_completion_mean, strength=100, size=n
    )
    ota_completion = _beta_samples(params.ota_completion_mean, strength=100, size=n)

    revenue_per_booking = _lognormal_samples(
        params.revenue_per_booking_mean, params.sigma, size=n
    )

    direct_bookings = direct_opps * direct_completion
    ota_bookings = ota_opps * ota_completion

    direct_capped, ota_capped, over_cap = _capacity_clip(
        direct_bookings, ota_bookings, params.capacity
    )

    revenue = direct_capped * revenue_per_booking
    revenue += ota_capped * revenue_per_booking * (1 - params.commission_rate)

    stats = {
        "mean": float(np.mean(revenue)),
        "p10": float(np.percentile(revenue, 10)),
        "p90": float(np.percentile(revenue, 90)),
    }

    capacity_stats = {
        "hit_rate": float(np.mean(over_cap)),
        "stranded": float(
            np.mean(
                np.maximum(direct_bookings + ota_bookings - params.capacity, 0)
                * params.revenue_per_booking_mean
            )
        ),
    }

    return revenue, stats, capacity_stats


def apply_intervention(params: SimulationParams) -> SimulationParams:
    shift = 0.1  # shift 10 percentage points from OTA to direct
    new_ota_share = max(0.0, params.ota_share - shift)
    new_direct_completion = min(0.95, params.direct_completion_mean * 1.05)
    new_revenue_mean = params.revenue_per_booking_mean * 1.05

    return SimulationParams(
        total_opportunities=params.total_opportunities,
        ota_share=new_ota_share,
        direct_completion_mean=new_direct_completion,
        ota_completion_mean=params.ota_completion_mean,
        revenue_per_booking_mean=new_revenue_mean,
        commission_rate=params.commission_rate,
        sigma=params.sigma,
        capacity=params.capacity,
        iterations=params.iterations,
        target_revenue=params.target_revenue,
    )


def run_sensitivity(params: SimulationParams):
    base_rev, base_stats, _ = simulate_revenue(params)
    base_mean = base_stats["mean"]

    scenarios = []

    def add(label: str, new_params: SimulationParams):
        rev, stats, _ = simulate_revenue(new_params)
        scenarios.append((label, stats["mean"] - base_mean))

    # Channel mix
    mix_delta = min(0.2, params.ota_share)
    add(
        "Reduce OTA share",
        params.__class__(
            **{**params.__dict__, "ota_share": params.ota_share - mix_delta}
        ),
    )

    # Commission rate
    comm_delta = 0.05
    add(
        "Reduce commission",
        params.__class__(
            **{
                **params.__dict__,
                "commission_rate": max(0.0, params.commission_rate - comm_delta),
            }
        ),
    )

    # Direct completion
    add(
        "Lift direct completion",
        params.__class__(
            **{
                **params.__dict__,
                "direct_completion_mean": min(
                    0.95, params.direct_completion_mean * 1.1
                ),
            }
        ),
    )

    # OTA completion
    add(
        "Lift OTA completion",
        params.__class__(
            **{
                **params.__dict__,
                "ota_completion_mean": min(0.99, params.ota_completion_mean * 1.05),
            }
        ),
    )

    # Revenue per booking
    add(
        "Increase revenue/booking",
        params.__class__(
            **{
                **params.__dict__,
                "revenue_per_booking_mean": params.revenue_per_booking_mean * 1.1,
            }
        ),
    )

    return sorted(scenarios, key=lambda x: abs(x[1]), reverse=True)
