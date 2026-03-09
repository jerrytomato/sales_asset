import numpy as np
import streamlit as st

from charts.histogram import revenue_histogram
from charts.probability import probability_indicator
from charts.sensitivity import sensitivity_chart
from model.funnel import deterministic_revenue
from model.monte_carlo import (
    SimulationParams,
    simulate_revenue,
    run_sensitivity,
    apply_intervention,
)


st.set_page_config(page_title="Revenue Risk Simulator", layout="wide")

if "revealed" not in st.session_state:
    st.session_state["revealed"] = False


def render_header():
    with st.container():
        st.title("Revenue Risk Simulator")
        st.write(
            "See how channel mix, commissions, and uncertainty shape your revenue distribution."
        )
        st.write(
            "Use this to learn how to reclaim margin from middlemen and raise the odds of hitting your targets."
        )


def render_deterministic_block(params: SimulationParams):
    with st.container():
        st.subheader("The single-number forecast (the lie)")
        det_rev = deterministic_revenue(
            demand=params.total_opportunities,
            ota_share=params.ota_share,
            direct_completion=params.direct_completion_mean,
            ota_completion=params.ota_completion_mean,
            revenue_per_booking=params.revenue_per_booking_mean,
            commission_rate=params.commission_rate,
            capacity=params.capacity,
        )
        cols = st.columns(3)
        cols[0].metric("Deterministic revenue", f"${det_rev:,.0f}")
        cols[1].metric("Direct completion", f"{params.direct_completion_mean:.0%}")
        cols[2].metric("OTA commission", f"{params.commission_rate:.0%}")


def render_inputs():
    with st.container():
        st.subheader("Inputs")
        left, right = st.columns([1, 1])

        with left:
            total_opportunities = st.number_input(
                "Total booking opportunities (this period)",
                min_value=50,
                max_value=100000,
                value=800,
                step=50,
                help="Total potential bookings across all channels for the selected period.",
            )
            ota_share = st.slider(
                "OTA / commissioned share (%)",
                min_value=0,
                max_value=100,
                value=40,
                step=1,
                help="Portion of booking opportunities routed through OTA/commission partners. Updates simulation live.",
            )
            direct_completion = st.slider(
                "Direct completion rate",
                min_value=0.05,
                max_value=0.9,
                value=0.3,
                step=0.01,
            )
            ota_completion = st.slider(
                "OTA completion rate",
                min_value=0.05,
                max_value=0.95,
                value=0.45,
                step=0.01,
            )
            capacity = st.number_input(
                "Capacity (bookings this period)",
                min_value=10,
                max_value=100000,
                value=500,
                step=10,
            )

        with right:
            revenue_per_booking = st.slider(
                "Average revenue per booking (before commission)",
                min_value=2000,
                max_value=10000,
                value=4000,
                step=250,
            )
            commission_rate = st.slider(
                "Commission rate (OTA)",
                min_value=0.0,
                max_value=0.4,
                value=0.20,
                step=0.01,
                help="Default 20%. Applied to OTA revenue only.",
            )
            sigma = st.slider(
                "Revenue volatility (lognormal sigma)",
                min_value=0.05,
                max_value=0.6,
                value=0.3,
                step=0.05,
                help="Controls spread of revenue per booking.",
            )
            target_revenue = st.number_input(
                "Target revenue",
                min_value=10000,
                max_value=20000000,
                value=150000,
                step=10000,
            )
            iterations = st.number_input(
                "Simulation iterations",
                min_value=10000,
                max_value=300000,
                value=100000,
                step=10000,
                help="More draws improve stability; 100k default.",
            )

    return SimulationParams(
        total_opportunities=total_opportunities,
        ota_share=ota_share / 100.0,
        direct_completion_mean=direct_completion,
        ota_completion_mean=ota_completion,
        revenue_per_booking_mean=revenue_per_booking,
        commission_rate=commission_rate,
        sigma=sigma,
        capacity=capacity,
        iterations=int(iterations),
        target_revenue=target_revenue,
    )


def render_results(
    params: SimulationParams,
    revenue: np.ndarray,
    stats: dict,
    target_prob: float,
    capacity_stats: dict,
    label: str,
):
    st.subheader(label)
    cols = st.columns(4)
    cols[0].metric("Mean", f"${stats['mean']:,.0f}")
    cols[1].metric("P10", f"${stats['p10']:,.0f}")
    cols[2].metric("P90", f"${stats['p90']:,.0f}")
    cols[3].metric("Hit target", f"{target_prob:.1%}")

    st.plotly_chart(
        revenue_histogram(revenue, stats),
        use_container_width=True,
        key=f"hist-{label}",
    )

    prob_fig = probability_indicator(target_prob)
    cap_note = f"Capacity hit in {capacity_stats['hit_rate']:.1%} of runs; stranded revenue est. ${capacity_stats['stranded']:,.0f}"
    c1, c2 = st.columns([1, 2])
    with c1:
        st.plotly_chart(prob_fig, use_container_width=True, key=f"prob-{label}")
    with c2:
        st.info(cap_note)


def main():
    render_header()
    params = render_inputs()

    render_deterministic_block(params)

    st.markdown("### Reveal reality")
    run_button = st.button("Run simulation", type="primary")
    if run_button:
        st.session_state["revealed"] = True

    if st.session_state["revealed"]:
        revenue, stats, capacity_stats = simulate_revenue(params)
        target_prob = np.mean(revenue >= params.target_revenue)
        render_results(
            params, revenue, stats, target_prob, capacity_stats, "Baseline distribution"
        )

        st.markdown("### Intervention toggle")
        enable_intervention = st.checkbox(
            "Show Direct Boost intervention",
            value=True,
            help="Shifts some OTA volume to direct, lifts direct completion, and improves add-ons slightly.",
        )
        if enable_intervention:
            boosted_params = apply_intervention(params)
            boosted_revenue, boosted_stats, boosted_capacity = simulate_revenue(
                boosted_params
            )
            boosted_prob = np.mean(boosted_revenue >= params.target_revenue)

            delta_cols = st.columns(4)
            delta_cols[0].metric(
                "Mean uplift", f"${boosted_stats['mean'] - stats['mean']:,.0f}"
            )
            delta_cols[1].metric(
                "P10 uplift", f"${boosted_stats['p10'] - stats['p10']:,.0f}"
            )
            delta_cols[2].metric(
                "Target prob delta", f"{boosted_prob - target_prob:+.1%}"
            )
            delta_cols[3].metric(
                "Capacity hit delta",
                f"{boosted_capacity['hit_rate'] - capacity_stats['hit_rate']:+.1%}",
            )

            render_results(
                boosted_params,
                boosted_revenue,
                boosted_stats,
                boosted_prob,
                boosted_capacity,
                "Intervention distribution",
            )

            st.markdown("### Sensitivity: what moves revenue risk")
            sens = run_sensitivity(params)
            st.plotly_chart(sensitivity_chart(sens), use_container_width=True)

        st.caption(
            "This demo uses 100k Monte Carlo draws by default. A custom model would match your exact seasonality, fleet, and channel contracts."
        )


if __name__ == "__main__":
    main()
