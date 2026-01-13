import streamlit as st
import pandas as pd
import os

# -----------------------------------------------------------------------------
# 1. SETUP & DATA LOADING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Customer Order History", layout="wide")

@st.cache_data
def load_data():
    # Helper function to read CSV or ZIP
    def read_file(base_filename):
        # 1. Try reading the raw CSV first
        if os.path.exists(base_filename):
            return pd.read_csv(base_filename)
        
        # 2. If not found, try reading the ZIP version
        zip_name = base_filename.replace('.csv', '.zip')
        if os.path.exists(zip_name):
            # Pandas can read directly from zip if it contains one file
            return pd.read_csv(zip_name)
        
        return None

    # Load the three specific files
    cust = read_file('Customers_64V94W6D22.csv')
    ordr = read_file('Orders_WUMZTNW4SS.csv')
    detl = read_file('OrderDetails_WUMZTNW4SS.csv')
    
    return cust, ordr, detl

customers_df, orders_df, order_details_df = load_data()

# -----------------------------------------------------------------------------
# 2. APP LAYOUT
# -----------------------------------------------------------------------------
st.title("🛍️ Customer History Search")
st.markdown("Type a customer's name below to see their profile and purchase history.")

# Check if data loaded correctly
if customers_df is None or orders_df is None or order_details_df is None:
    st.error("""
    ⚠️ **Data files not found!** Please upload your files to the GitHub repository. 
    You can upload them as `.csv` OR `.zip` files.
    
    Expected filenames (or their .zip equivalents):
    * `Customers_64V94W6D22.csv`
    * `Orders_WUMZTNW4SS.csv`
    * `OrderDetails_WUMZTNW4SS.csv`
    """)
    st.stop()

# Search Bar
search_name = st.text_input("Enter Customer Name (First or Last):", "")

# -----------------------------------------------------------------------------
# 3. SEARCH LOGIC
# -----------------------------------------------------------------------------
if search_name:
    # Filter Customers (Case insensitive)
    # ensuring string type for robustness
    mask = (customers_df['firstname'].astype(str).str.contains(search_name, case=False, na=False)) | \
           (customers_df['lastname'].astype(str).str.contains(search_name, case=False, na=False))
    
    found_customers = customers_df[mask]

    if found_customers.empty:
        st.warning("No customers found with that name.")
    else:
        st.success(f"Found {len(found_customers)} customer(s).")
        
        # Iterate through each found customer
        for index, customer in found_customers.iterrows():
            cust_id = customer['customerid']
            # Handle potential missing name values
            f_name = str(customer['firstname']) if pd.notna(customer['firstname']) else ""
            l_name = str(customer['lastname']) if pd.notna(customer['lastname']) else ""
            full_name = f"{f_name} {l_name}".strip()
            
            email = customer['emailaddress']
            phone = customer['phonenumber']
            
            # Format address cleanly
            addr_parts = [
                str(customer['billingaddress1']) if pd.notna(customer['billingaddress1']) else "",
                str(customer['billingcity']) if pd.notna(customer['billingcity']) else "",
                str(customer['billingstate']) if pd.notna(customer['billingstate']) else ""
            ]
            address = ", ".join([p for p in addr_parts if p])
            
            with st.expander(f"👤 {full_name} ({email})", expanded=True):
                # Display Customer Details
                col1, col2 = st.columns(2)
                col1.write(f"**Phone:** {phone}")
                col2.write(f"**Address:** {address}")
                
                # Get Orders for this customer
                cust_orders = orders_df[orders_df['customerid'] == cust_id]
                
                if cust_orders.empty:
                    st.info("No orders on file for this customer.")
                else:
                    st.markdown("### 📦 Order History")
                    
                    # Merge Orders with Order Details
                    history = pd.merge(
                        cust_orders[['orderid', 'orderdate', 'totalshippingcost', 'paymentamount', 'orderstatus']],
                        order_details_df[['orderid', 'productname', 'quantity', 'totalprice']],
                        on='orderid',
                        how='inner'
                    )
                    
                    if history.empty:
                        st.write("Orders found, but no product details available.")
                    else:
                        # Clean up the table for display
                        display_table = history.rename(columns={
                            'orderdate': 'Date',
                            'orderstatus': 'Status',
                            'productname': 'Product',
                            'quantity': 'Qty',
                            'totalprice': 'Item Price',
                            'paymentamount': 'Order Total'
                        })
                        
                        # Show the table
                        st.dataframe(
                            display_table[['Date', 'Status', 'Product', 'Qty', 'Item Price', 'Order Total']],
                            use_container_width=True,
                            hide_index=True
                        )