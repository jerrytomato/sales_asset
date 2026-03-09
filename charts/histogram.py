import numpy as np
import plotly.graph_objects as go


def revenue_histogram(revenue: np.ndarray, stats: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=revenue,
            nbinsx=40,
            marker_color="#3182ce",
            opacity=0.75,
            hovertemplate="$%{x:,.0f}<extra></extra>",
        )
    )

    for name, color in [("p10", "#f56565"), ("mean", "#2f855a"), ("p90", "#ed8936")]:
        fig.add_vline(
            x=stats[name],
            line_width=2,
            line_dash="dash",
            line_color=color,
            annotation_text=name.upper(),
            annotation_position="top",
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        bargap=0.05,
        template="simple_white",
        xaxis_title="Revenue",
        yaxis_title="Frequency",
    )
    return fig
