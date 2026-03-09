import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Polygon Visualization from CSV")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file (must contain STN, E, and N columns)", type=["csv"])

if uploaded_file is not None:
    # Read CSV
    df = pd.read_csv(uploaded_file)
    
    # Check if necessary columns exist
    if all(col in df.columns for col in ['STN', 'E', 'N']):
        st.subheader("Data Preview")
        st.write(df)

        # Close the polygon by appending the first point to the end
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # Plotting
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(df_poly['E'], df_poly['N'], marker='o', linestyle='-', color='b')
        
        # Label each station
        for i, txt in enumerate(df['STN']):
            ax.annotate(txt, (df['E'].iloc[i], df['N'].iloc[i]), 
                        textcoords="offset points", xytext=(0,10), ha='center')

        ax.set_xlabel('Easting (E)')
        ax.set_ylabel('Northing (N)')
        ax.set_title('Polygon Plot')
        ax.grid(True)
        ax.set_aspect('equal', adjustable='box')

        # Show plot in Streamlit
        st.pyplot(fig)
        
        # Optional: Calculate Perimeter
        # You could also add Shoelace formula for Area here
    else:
        st.error("CSV must contain columns named 'STN', 'E', and 'N'.")
else:
    st.info("Please upload a CSV file to see the polygon.")
