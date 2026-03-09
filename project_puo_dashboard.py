import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("Interactive Polygon (Easting & Northing)")

uploaded_file = st.file_uploader("Upload CSV (STN, E, N)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if all(col in df.columns for col in ['STN','E','N']):

        st.subheader("Data Preview")
        st.write(df)

        # Close polygon
        df_poly = pd.concat([df, df.iloc[[0]]])

        fig = go.Figure()

        # Polygon line
        fig.add_trace(go.Scatter(
            x=df_poly['E'],
            y=df_poly['N'],
            mode='lines+markers',
            name='Polygon',
            line=dict(color='blue'),
            marker=dict(size=8)
        ))

        # Add station labels
        for i, txt in enumerate(df['STN']):
            fig.add_annotation(
                x=df['E'][i],
                y=df['N'][i],
                text=txt,
                showarrow=True,
                arrowhead=1
            )

        fig.update_layout(
            xaxis_title='Easting (m)',
            yaxis_title='Northing (m)',
            title='Interactive Polygon Plot',
            yaxis=dict(scaleanchor="x", scaleratio=1),  # keep aspect ratio 1:1
            width=700,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("CSV must contain STN, E, N columns")

