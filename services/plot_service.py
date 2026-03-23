import plotly.express as px
import pandas as pd


def build_pm25_timeseries_plot(df: pd.DataFrame):
    if df.empty:
        return None

    fig = px.line(
        df,
        x="date",
        y="pm25",
        color="city",
        markers=True,
        labels={
            "date": "Date",
            "pm25": "PM2.5 (µg/m³)",
            "city": "Location",
        },
        title="Daily Average PM2.5 Comparison",
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="PM2.5 (µg/m³)",
        legend_title="Location",
    )
    return fig