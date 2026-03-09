import plotly.graph_objects as go


def sensitivity_chart(scenarios: list[tuple[str, float]]) -> go.Figure:
    labels = [s[0] for s in scenarios]
    deltas = [s[1] for s in scenarios]
    colors = ["#2f855a" if d >= 0 else "#c53030" for d in deltas]

    fig = go.Figure(
        go.Bar(
            x=deltas,
            y=labels,
            orientation="h",
            marker_color=colors,
            hovertemplate="$%{x:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Mean revenue change vs baseline",
        xaxis_title="Delta ($)",
        margin=dict(l=120, r=10, t=40, b=40),
        template="simple_white",
    )
    return fig
