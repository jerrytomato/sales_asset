import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Revenue Risk Simulator", layout="wide")


def beta_pdf(mean: float, strength: float = 80, points: int = 400):
    mean = np.clip(mean, 1e-4, 1 - 1e-4)
    alpha = mean * strength
    beta = (1 - mean) * strength
    x = np.linspace(0, 1, points)
    raw = np.power(x, alpha - 1) * np.power(1 - x, beta - 1)
    dx = x[1] - x[0]
    norm = raw.sum() * dx
    pdf = raw / norm if norm > 0 else raw
    return x, pdf


def vertical_line_chart(value: float) -> go.Figure:
    fig = go.Figure()
    fig.add_shape(
        type="line",
        x0=value,
        x1=value,
        y0=0,
        y1=1,
        line=dict(color="#2f855a", width=4),
    )
    fig.update_yaxes(visible=False, range=[0, 1])
    fig.update_xaxes(range=[0, 1], title="Conversion rate", tickformat=".0%", dtick=0.1)
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=40),
        template="simple_white",
        height=240,
        title="Point forecast (one number)",
        showlegend=False,
    )
    fig.add_annotation(
        x=value,
        y=0.5,
        text=f"{value:.0%}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#2f855a",
    )
    return fig


def beta_chart(value: float, strength: float = 80) -> go.Figure:
    x, pdf = beta_pdf(value, strength=strength)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=x, y=pdf, mode="lines", line=dict(color="#3182ce", width=3))
    )
    fig.add_shape(
        type="line",
        x0=value,
        x1=value,
        y0=0,
        y1=max(pdf) if len(pdf) else 1,
        line=dict(color="#e53e3e", width=2, dash="dash"),
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=40),
        template="simple_white",
        height=320,
        title="Distribution (uncertainty)",
        xaxis_title="Conversion rate",
        yaxis_title="Probability density",
        showlegend=False,
    )
    fig.update_xaxes(tickformat=".0%", dtick=0.1)
    return fig


def main():
    st.session_state.setdefault("conv", 0.3)
    st.session_state.setdefault("strength", 80)

    col = st.columns([0.25, 0.5, 0.25])[1]
    with col:
        st.title("How Data Lies and Kills Decision Making")
        st.write(
            "A single conversion rate is a guess. A distribution shows the uncertainty around it."
        )
        st.write(
            "Start with the point estimate, then see how uncertainty tightens or widens outcomes."
        )

        st.subheader("1) The lie (point forecast)")
        st.markdown(
            "- One fixed conversion rate assumes everyone behaves the same\n- Hides upside and downside"
        )
        st.write(
            "The vertical line below is the point forecast. It never shows how much outcomes can vary."
        )

        st.subheader("2) Pick your conversion and certainty")
        conv = st.slider(
            "Conversion rate (mean)",
            min_value=0.01,
            max_value=0.9,
            value=float(st.session_state.get("conv", 0.3)),
            step=0.01,
            key="conv",
        )
        strength = st.slider(
            "Certainty (higher = tighter)",
            min_value=10,
            max_value=200,
            value=int(st.session_state.get("strength", 80)),
            step=5,
            help="Controls how concentrated the distribution is around the mean.",
            key="strength",
        )
        conv = st.session_state.get("conv", conv)
        strength = st.session_state.get("strength", strength)

        st.subheader("3) See the difference")
        st.write(
            "The same mean, shown as a single point and as a distribution that breathes with certainty."
        )
        st.markdown("**Point forecast**")
        st.plotly_chart(vertical_line_chart(conv), width="stretch")
        st.markdown("**Uncertainty (beta distribution)**")
        st.plotly_chart(beta_chart(conv, strength=strength), width="stretch")

        st.markdown("#### What to notice")
        st.markdown(
            "The line is the lie. The curve is reality: many possible outcomes around your best guess. Higher certainty tightens the curve; lower certainty widens it."
        )


if __name__ == "__main__":
    main()
