import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path
import plotly.express as px
import seaborn as sns
from urllib.parse import quote

current_dir = Path(__file__).parent

# Aiven Cloud MySQL Connection Configuration
DB_CONFIG = {
    "host": "mysql-a60948b-sathya41195-1055.d.aivencloud.com",
    "user": "avnadmin",
    "password": "AVNS_6U99Jq6I3A9FqHqTRCz",
    "database": "guvi_projects",
    "port": "13687"
}

def get_engine():
    conn_str = f"mysql+pymysql://{DB_CONFIG['user']}:{quote(DB_CONFIG['password'])}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_str)

def upload_to_mysql(df, table_name):
    engine = get_engine()
    df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)

def run_sql_query(query):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# -----------------------------------------------------------------------------
# GLOBAL SIDEBAR FILTERS (Executes filtering completely via SQL)
# -----------------------------------------------------------------------------
st.sidebar.title("🌍 Dashboard Controls")
st.sidebar.markdown("Use these parameters to query the remote database directly.")

selected_segments = st.sidebar.multiselect(
    "Development Segment",
    ['High Risk Country', 'Developed Nation', 'Emerging Economy', 'High Inflation Risk', 'Health Critical', 'Low GDP Trap', 'Other'],
    default=['High Risk Country', 'Developed Nation', 'Emerging Economy']
)

income_range = st.sidebar.slider("Income Range ($)", 400, 150000, (500, 50000))
inflation_range = st.sidebar.slider("Inflation Range (%)", -5.0, 110.0, (-2.0, 50.0))
fertility_range = st.sidebar.slider("Fertility Rate", 1.0, 10.0, (1.0, 8.0))

# Constructing the dynamic SQL WHERE statement
seg_filter = ", ".join(f"'{s}'" for s in selected_segments) if selected_segments else "'Other'"
sql_where_clause = f""" 
    WHERE segment IN ({seg_filter}) 
    AND income BETWEEN {income_range[0]} AND {income_range[1]}
    AND inflation BETWEEN {inflation_range[0]} AND {inflation_range[1]}
    AND total_fer BETWEEN {fertility_range[0]} AND {fertility_range[1]}
"""

# Fetch filtered dataframe from remote database instance
try:
    df_filtered = run_sql_query(f"SELECT * FROM country_data {sql_where_clause}")
except Exception:
    # Fallback structure if the table hasn't been written yet
    st.sidebar.warning("Database empty or table missing. Click 'Push to Database' below.")
    df_filtered = pd.DataFrame()

# -----------------------------------------------------------------------------
# APPLICATION TABS SETUP
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Global Overview", "Health & Economic Risk", "Segmentation Insights"])    

with tab1:
    st.subheader("System Performance & Overview")
    
    col_upload, col_uni, col_bi, col_corr = st.columns(4)
    with col_upload:
        if st.button("🚀 Push Raw Data to DB"):
            try:
                # Load, process, and write reference copy to server
                csv_path = (current_dir / '..' / 'source_data' / 'Country_data.csv').resolve()
                raw_data = pd.read_csv(csv_path)
                
                # Outlier logic - Applied IQR majority of the data's look like skewed
                for col in ["income", "gdpp", "child_mort", "inflation"]:
                    q25, q75 = raw_data[col].quantile(0.25), raw_data[col].quantile(0.75)
                    iqr = q75 - q25
                    raw_data[col] = raw_data[col].clip(q25 - 1.5*iqr, q75 + 1.5*iqr)
                
                # Rule-based segmentation assignment
                conditions = [
                    (raw_data['child_mort'] > 80) & (raw_data['income'] < 5000),
                    (raw_data['income'] > 30000) & (raw_data['life_expec'] > 78),
                    (raw_data['income'] > 8000) & (raw_data['income'] < 30000),
                    (raw_data['inflation'] > 15),
                    (raw_data['health'] < 5) & (raw_data['child_mort'] > 70),
                    (raw_data['gdpp'] < 2000)
                ]
                choices = ['High Risk Country', 'Developed Nation', 'Emerging Economy', 'High Inflation Risk', 'Health Critical', 'Low GDP Trap']
                raw_data['segment'] = np.select(conditions, choices, default='Other')
                                
                #Feature engineering
                raw_data['Development_Index'] = (raw_data['income'] + raw_data['gdpp'] + raw_data['life_expec']) / raw_data['child_mort']
                raw_data['Trade_Balance'] = raw_data['exports'] - raw_data['imports']
                raw_data['Health_Impact_Ratio'] = raw_data['health'] / raw_data['child_mort']
                raw_data['Risk_flag'] = raw_data['segment'].isin(['High Risk Country', 'High Inflation Risk', 'Health Critical', 'Low GDP Trap']).astype(int)                
                upload_to_mysql(raw_data, 'country_data')
                st.success("Database successfully synchronized!")
                st.rerun()
            except Exception as e:
                st.error(f"Synchronization Failed: {e}")

    # Render Dialog Modals using current SQL database slice
    if not df_filtered.empty:
        with col_uni:
            @st.dialog("Univariate Analysis Distributions", width="large")
            def univariate():
                fig, axes = plt.subplots(2, 3, figsize=(15, 10))
                cols = ["income", "child_mort", "life_expec", "gdpp", "total_fer", "inflation"]
                for ax, col in zip(axes.flat, cols):
                    sns.histplot(df_filtered[col], kde=True, ax=ax, bins=20, color="teal")
                    ax.set_title(f"Spread: {col}")
                plt.tight_layout()
                st.pyplot(fig)
            if st.button("📈 Run Univariate"): univariate()

        with col_bi:
            @st.dialog("Bivariate Correlation Analysis", width="large")
            def bivariate():
                fig, axes = plt.subplots(2, 3, figsize=(15, 10))
                plots = [
                    ("income", "life_expec", "Income vs Life Expectancy"),
                    ("health", "child_mort", "Health Spend vs Child Mort"),
                    ("gdpp", "total_fer", "GDP vs Fertility"),
                    ("inflation", "gdpp", "Inflation vs GDP"),
                    ("Trade_Balance", "income", "Trade Balance vs Income"),
                    ("Health_Impact_Ratio", "life_expec", "Health Impact vs Life Expectancy"),
                ]
                for ax, (x, y, title) in zip(axes.flat, plots):
                    sns.scatterplot(data=df_filtered, x=x, y=y, hue="segment", ax=ax, alpha=0.8)
                    ax.set_title(title)
                plt.tight_layout()
                st.pyplot(fig)
            if st.button("📉 Run Bivariate"): bivariate()

        with col_corr:
            @st.dialog("System Matrix Heatmap", width="medium")
            def correlation():
                numeric_cols = ["child_mort", "exports", "health", "imports", "income", "inflation", "life_expec", "total_fer", "gdpp"]
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(df_filtered[numeric_cols].corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
                st.pyplot(fig)
            if st.button("📊 Run Correlation Matrix"): correlation()

        # Dynamic KPI Card Elements
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg Income Pool", f"${df_filtered['income'].mean()/1000:,.2f}k", border=True)
        m2.metric("Avg Life Expectancy", f"{df_filtered['life_expec'].mean():.1f} Yrs", border=True)
        m3.metric("Avg Child Mortality", f"{df_filtered['child_mort'].mean():.1f}", border=True)
        m4.metric("Active High-Risk Count", int(df_filtered['Risk_flag'].sum()), border=True)

        # Choropleth Map Visualizations
        st.plotly_chart(px.choropleth(df_filtered, locations='country', locationmode='country names', color='segment', title='Global Segments Map Matrix (Filtered SQL)'), use_container_width=True)
        st.plotly_chart(px.scatter(df_filtered, x='income', y='life_expec', color='segment', hover_name='country', title='Life Expectancy over Income Per Capita Base'), use_container_width=True)
    else:
        st.info("Adjust the sidebar filters to pull data rows from your SQL instance.")

with tab2:
    st.subheader("Micro-Health Framework Metrics")
    if not df_filtered.empty:
        # Avoid chart crowding by showing top 20 vulnerability zones
        df_sorted_mort = df_filtered.sort_values(by='child_mort', ascending=False)    
        df_sorted_mort['rank_type'] = 'Other'
        df_sorted_mort.iloc[:10, df_sorted_mort.columns.get_loc('rank_type')] = 'Top 10'
        df_sorted_mort.iloc[-10:, df_sorted_mort.columns.get_loc('rank_type')] = 'Bottom 10'
        st.plotly_chart(px.bar(df_sorted_mort, x='country', y='child_mort', color='rank_type', title='Child Mortality Performance Rankings'), use_container_width=True)
        
        st.plotly_chart(px.scatter(df_filtered, x='health', y='child_mort', color='segment', trendline="ols", title='Healthcare Infrastructure Capital Input Effectiveness vs Mortality Rates'), use_container_width=True)
        
        # Cleaned up inflation plot
        df_sorted_inf = df_filtered.sort_values(by='inflation', ascending=False)
        df_sorted_inf['rank_type'] = 'Other'
        df_sorted_inf.iloc[:10, df_sorted_inf.columns.get_loc('rank_type')] = 'Top 10'
        df_sorted_inf.iloc[-10:, df_sorted_inf.columns.get_loc('rank_type')] = 'Bottom 10'
        st.plotly_chart(px.bar(df_sorted_inf, x='country', y='inflation', color='rank_type', title='Macroeconomic Volatility Spikes'), use_container_width=True)
        
        st.plotly_chart(px.scatter(df_filtered, x="gdpp", y="total_fer", size="child_mort", color="segment", hover_name="country", title="Economic Capacity Output Framework vs Fertility Metrics"), use_container_width=True)

with tab3:
    st.subheader("Statistical Cluster Insights & Data Inventory")
    if not df_filtered.empty:
        c1, c2, c3 = st.columns(3)
        
        with c1:
            counts = df_filtered['segment'].value_counts().reset_index()
            st.plotly_chart(px.pie(counts, values='count', names='segment', hole=0.4, title='Macro System Segment Composition'), use_container_width=True)
            
        with c2:
            avg_inc = df_filtered.groupby('segment')['income'].mean().reset_index()
            st.plotly_chart(px.bar(avg_inc, x='segment', y='income', color='segment', title='Mean Income Profile'), use_container_width=True)
            
        with c3:
            avg_gdp = df_filtered.groupby('segment')['gdpp'].mean().reset_index()
            st.plotly_chart(px.bar(avg_gdp, x='segment', y='gdpp', color='segment', title='Mean GDP per Capita Profile'), use_container_width=True)
            
        st.markdown("---")
        st.subheader("Targeted Data View Matrix")
        st.dataframe(df_filtered, use_container_width=True)