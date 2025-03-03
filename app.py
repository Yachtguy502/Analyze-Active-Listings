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
        return None, None, None, None, None
    
    required_columns = ["Engine Hours", "Valid HIN?", "Display Price", "Make", "Model", "Images"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing columns in CSV: {', '.join(missing_columns)}")
        return None, None, None, None, None
    
    engine_hours_col = "Engine Hours"
    missing_engine_hours = df[df[engine_hours_col].isna()][["Make", "Model"]]
    
    hin_col = "Valid HIN?"
    invalid_hin_boats = df[df[hin_col] != "Yes"][["Make", "Model"]]
    
    display_price_col = "Display Price"
    missing_display_price = df[df[display_price_col].isna()][["Make", "Model"]]
    
    images_col = "Images"
    low_image_boats = df[df[images_col] < 10][["Make", "Model"]]
    
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
    
    return summary_df, missing_engine_hours, invalid_hin_boats, missing_display_price, low_image_boats

def main():
    st.title("Boat Inventory Analysis Tool")
    uploaded_file = st.file_uploader("Upload Active Listings CSV", type=["csv"])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            summary_df, missing_engine_hours, invalid_hin_boats, missing_display_price, low_image_boats = process_data(df)
            
            if summary_df is not None:
                total_bt = summary_df[['BT Advantage', 'BT Plus', 'BT Select']].sum().sum()
                total_yw = summary_df[['YW Advantage', 'YW Plus', 'YW Select']].sum().sum()
                
                st.subheader("Total Membership Revenue")
                st.markdown(f"### **Total BoatTrader Revenue: ${total_bt:,.2f}**")
                st.markdown(f"### **Total YachtWorld Revenue: ${total_yw:,.2f}**")
                
                st.subheader("Price Breakdown by Tier")
                st.dataframe(summary_df)
                
                if st.button("Download Excel Report"):
                    with pd.ExcelWriter("boat_inventory_report.xlsx") as writer:
                        summary_df.to_excel(writer, sheet_name="Price Bands", index=False)
                        missing_engine_hours.to_excel(writer, sheet_name="Missing Engine Hours", index=False)
                        invalid_hin_boats.to_excel(writer, sheet_name="Invalid HIN", index=False)
                        missing_display_price.to_excel(writer, sheet_name="Missing Display Price", index=False)
                        low_image_boats.to_excel(writer, sheet_name="Low Images", index=False)
                    
                    st.success("Excel report has been generated and is ready for download.")
            
            st.subheader("Additional Data Insights")
            if missing_engine_hours is not None:
                st.subheader("Boats with Missing Engine Hours")
                st.dataframe(missing_engine_hours)
            
            if invalid_hin_boats is not None:
                st.subheader("Boats with Invalid HIN Numbers")
                st.dataframe(invalid_hin_boats)
            
            if missing_display_price is not None:
                st.subheader("Boats with Missing Display Price")
                st.dataframe(missing_display_price)
            
            if low_image_boats is not None:
                st.subheader("Boats with Fewer than 10 Images")
                st.dataframe(low_image_boats)

if __name__ == "__main__":
    main()

