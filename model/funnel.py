import numpy as np


def clamp01(x: np.ndarray | float) -> np.ndarray | float:
    return np.clip(x, 0.0, 1.0)


def deterministic_revenue(
    demand: float,
    ota_share: float,
    direct_completion: float,
    ota_completion: float,
    revenue_per_booking: float,
    commission_rate: float,
    capacity: float,
) -> float:
    ota_share = clamp01(ota_share)
    direct_share = 1 - ota_share
    direct_bookings = demand * direct_share * direct_completion
    ota_bookings = demand * ota_share * ota_completion

    total_bookings = direct_bookings + ota_bookings
    if total_bookings == 0:
        return 0.0

    cap = min(capacity, total_bookings)
    if total_bookings > 0:
        direct_ratio = direct_bookings / total_bookings
    else:
        direct_ratio = 0
    ota_ratio = 1 - direct_ratio

    direct_capped = cap * direct_ratio
    ota_capped = cap * ota_ratio

    direct_rev = direct_capped * revenue_per_booking
    ota_rev = ota_capped * revenue_per_booking * (1 - commission_rate)
    return float(direct_rev + ota_rev)
