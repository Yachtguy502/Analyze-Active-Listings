import streamlit as st
import pandas as pd

def load_data(file):
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def process_data(df):
    if df is None:
        return None, None, None
    
    required_columns = ["Engine Hours", "Valid HIN?", "Display Price", "Make", "Model"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing columns in CSV: {', '.join(missing_columns)}")
        return None, None, None
    
    engine_hours_col = "Engine Hours"
    missing_engine_hours = df[df[engine_hours_col].isna()][["Make", "Model"]]
    
    hin_col = "Valid HIN?"
    invalid_hin_boats = df[df[hin_col] != "Yes"][["Make", "Model"]]
    
    price_bands = {
        "Under $10K": (0, 10000), "$10K-$25K": (10000, 25000), "$25K-$50K": (25000, 50000),
        "$50K-$75K": (50000, 75000), "$75K-$100K": (75000, 100000), "$100K-$250K": (100000, 250000),
        "$250K-$500K": (250000, 500000), "$500K-$1M": (500000, 1000000), "$1M-$5M": (1000000, 5000000),
        "Over $5M": (5000000, float('inf'))
    }
    
    df["Display Price"] = pd.to_numeric(df["Display Price"], errors='coerce')
    df["Price Band"] = df["Display Price"].apply(lambda x: next((band for band, (low, high) in price_bands.items() if low <= x < high), "Unknown"))
    price_band_counts = df["Price Band"].value_counts().reindex(price_bands.keys(), fill_value=0)
    
    summary_df = pd.DataFrame({
        "Price Band": price_band_counts.index,
        "Boat Count": price_band_counts.values
    })
    
    bt_yw_prices = {
        "Under $10K": (10, 100), "$10K-$25K": (25, 100), "$25K-$50K": (50, 100), "$50K-$75K": (75, 100),
        "$75K-$100K": (100, 100), "$100K-$250K": (125, 125), "$250K-$500K": (150, 150), "$500K-$1M": (200, 200),
        "$1M-$5M": (500, 500), "Over $5M": (1000, 1000)
    }
    
    summary_df["BT Advantage"] = summary_df["Price Band"].apply(lambda x: bt_yw_prices.get(x, (0, 0))[0] * summary_df.loc[summary_df["Price Band"] == x, "Boat Count"].values[0])
    summary_df["BT Plus"] = summary_df["BT Advantage"] * 1.25
    summary_df["BT Select"] = summary_df["BT Advantage"] * 1.50
    
    summary_df["YW Advantage"] = summary_df["Price Band"].apply(lambda x: bt_yw_prices.get(x, (0, 0))[1] * summary_df.loc[summary_df["Price Band"] == x, "Boat Count"].values[0])
    summary_df["YW Plus"] = summary_df["YW Advantage"] * 1.25
    summary_df["YW Select"] = summary_df["YW Advantage"] * 1.50
    
    return summary_df, missing_engine_hours, invalid_hin_boats

def main():
    st.title("Boat Inventory Analysis Tool")
    uploaded_file = st.file_uploader("Upload Active Listings CSV", type=["csv"])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            summary_df, missing_engine_hours, invalid_hin_boats = process_data(df)
            
            if summary_df is not None:
                st.subheader("Price Band Summary")
                st.dataframe(summary_df)
            
            if missing_engine_hours is not None:
                st.subheader("Boats with Missing Engine Hours")
                st.dataframe(missing_engine_hours)
            
            if invalid_hin_boats is not None:
                st.subheader("Boats with Invalid HIN Numbers")
                st.dataframe(invalid_hin_boats)

if __name__ == "__main__":
    main()
