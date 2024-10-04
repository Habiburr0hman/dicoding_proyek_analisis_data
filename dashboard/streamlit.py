import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import seaborn as sns
import pandas as pd
from babel.numbers import format_currency
import streamlit as st
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
sns.set(style='dark')

all_df = pd.read_csv('dashboard/main_data.csv')

datetime_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'review_answer_timestamp', 'order_purchase_date']
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

def create_customer_by_state_df(df):
    customer_by_state_df = df.groupby('customer_state')['customer_unique_id'].nunique().sort_values(ascending=False).reset_index()
    return customer_by_state_df

def create_customer_by_city_df(df):
    customer_by_city_df = df.groupby('customer_city')['customer_unique_id'].nunique().sort_values(ascending=False).reset_index()
    return customer_by_city_df

def create_daily_order_df(df):
    daily_order_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    daily_order_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue",
        "order_purchase_timestamp": "order_date"
    }, inplace=True)

    return daily_order_df

def create_sum_order_item_category_df(df):
    sum_order_item_category_df = df.groupby('product_category_name_english').agg({
        'order_item_id': 'count'
    }).reset_index()

    return sum_order_item_category_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_uid", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"]
    recent_date = all_df["order_purchase_timestamp"].max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).total_seconds() / 3600)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df

min_date = all_df['order_purchase_date'].min()
max_date = all_df['order_purchase_date'].max()
with st.sidebar:
    st.image("img/olist_icon.png")
    start_date, end_date = st.date_input(
        label = 'Select Date Range', min_value = min_date,
        max_value = max_date,
        value = [min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_date"] >= str(start_date)) & 
                (all_df["order_purchase_date"] <= str(end_date))]
main_df_unique_order_item = main_df.drop_duplicates(subset=['order_id', 'order_item_id'])

customer_by_state_df = create_customer_by_state_df(main_df)
customer_by_city_df = create_customer_by_city_df(main_df)
daily_order_df = create_daily_order_df(main_df_unique_order_item)
sum_order_item_category_df = create_sum_order_item_category_df(main_df_unique_order_item)
rfm_df = create_rfm_df(main_df_unique_order_item)


st.header('Olist E-Commerce Dashboard')


st.subheader('Daily Order and Revenue')

col1, col2 = st.columns(2)
with col1:
    total_orders = daily_order_df['order_count'].sum()
    st.metric("Total Order", value=total_orders)
with col2:
    total_revenue = format_currency(daily_order_df['revenue'].sum(), 'R$ ', locale='en_US') 
    st.metric("Total Revenue", value=total_revenue)
 
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(
    daily_order_df['order_date'],
    daily_order_df['order_count'],
    marker = 'o', 
    linewidth = 2,
    color = 'blue'
)
ax.set_title("Daily Order", loc="center", fontsize=20)
ax.set_xlabel('Date', fontsize=18)
ax.set_ylabel('Orders', fontsize=18)
ax.tick_params(axis='y', labelsize=16)
ax.tick_params(axis='x', labelsize=14)
ax.grid()
st.pyplot(fig)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(
    daily_order_df["order_date"],
    daily_order_df["revenue"],
    marker = 'o',
    linewidth = 2,
    color = 'blue'
)
ax.set_title("Daily Revenue", loc="center", fontsize=18)
ax.set_xlabel('Date', fontsize=18)
ax.set_ylabel('Revenue', fontsize=18)
ax.tick_params(axis='y', labelsize=16)
ax.tick_params(axis='x', labelsize=14)
formatter = ScalarFormatter()
formatter.set_scientific(False)
ax.yaxis.set_major_formatter(formatter)
ax.grid()
st.pyplot(fig)


st.subheader("Best and Worst Performing Product Category") 

colors = ["blue", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
fig, ax = plt.subplots(figsize=(14, 6))
sns.barplot(data=sum_order_item_category_df.sort_values(by='order_item_id', ascending=False).head(5), x="order_item_id", y="product_category_name_english", palette=colors, ax=ax)
ax.set_ylabel(None)
ax.set_xlabel('Number of Order', fontsize=18)
ax.set_title("Best Performing Product Category", loc="center", fontsize=20)
ax.tick_params(axis ='x', labelsize=18)
ax.tick_params(axis ='y', labelsize=18)
st.pyplot(fig)

fig, ax = plt.subplots(figsize=(14, 6))
sns.barplot(data=sum_order_item_category_df.sort_values(by='order_item_id', ascending=True).head(5), x="order_item_id", y="product_category_name_english", palette=colors, ax=ax)
ax.set_ylabel(None)
ax.set_xlabel('Number of Order', fontsize=18)
ax.set_title("Worst Performing Product Category", loc="center", fontsize=20)
ax.tick_params(axis='x', labelsize=18)
ax.tick_params(axis='y', labelsize=18)
st.pyplot(fig)

st.subheader("Top Customer's Origin")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    x = "customer_state",
    y = "customer_unique_id",
    data = customer_by_state_df.sort_values(by='customer_unique_id', ascending=False)[:10],
    color = 'blue'
)
plt.title("Number of Customer by State (10 Highest)", loc="center", fontsize=16)
plt.xlabel('State', fontsize=14)
plt.ylabel('Customers', fontsize=14)
plt.grid(axis='y')
st.pyplot(fig)


fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    ax = ax, 
    x = "customer_unique_id",
    y = "customer_city",
    data = customer_by_city_df.sort_values(by='customer_unique_id', ascending=False)[:10],
    color = 'blue',
    orient = 'horizontal'
)
plt.title("Number of Customer by City (10 Highest)", loc="center", fontsize=16)
plt.xlabel('Customers', fontsize=14)
plt.ylabel('City', fontsize=14)
st.pyplot(fig)

