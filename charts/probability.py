import plotly.graph_objects as go


def probability_indicator(prob: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=prob * 100,
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2f855a"},
                "steps": [
                    {"range": [0, 50], "color": "#fed7d7"},
                    {"range": [50, 80], "color": "#fefcbf"},
                    {"range": [80, 100], "color": "#c6f6d5"},
                ],
            },
            title={"text": "Hit target"},
        )
    )
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=10))
    return fig
