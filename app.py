import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

ROOT=Path(__file__).parent
def load(name):
    p=ROOT/"data"/name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

brand=load("branded_medicines.csv")
gen=load("generic_medicines.csv")

st.set_page_config(page_title="Pharma Price Analytics",layout="wide")
st.title("Pharmaceutical Branded vs Government Generic Analytics")
st.caption("Seed files are verified source records; run scripts/data_collection.py to refresh live branded data and PMBI generic CSV.")

c1,c2,c3,c4=st.columns(4)
c1.metric("Branded entries",len(brand))
c2.metric("Government generic entries",len(gen))
c3.metric("Branded manufacturers",brand["manufacturer"].nunique() if "manufacturer" in brand else 0)
c4.metric("Generic therapeutic groups",gen["therapeutic_group"].nunique() if "therapeutic_group" in gen else 0)

tab1,tab2,tab3=st.tabs(["Overview","Price comparison","Source data"])
with tab1:
    if not brand.empty:
        st.subheader("Branded MRP by active salt")
        b=brand.dropna(subset=["mrp_inr"]).groupby("active_salt_composition",as_index=False)["mrp_inr"].mean().sort_values("mrp_inr",ascending=False)
        st.plotly_chart(px.bar(b,x="active_salt_composition",y="mrp_inr",title="Average branded MRP"),use_container_width=True)
    if not gen.empty:
        g=gen.groupby("therapeutic_group",as_index=False).size().sort_values("size",ascending=False)
        st.plotly_chart(px.bar(g,x="therapeutic_group",y="size",title="Government generic entries by therapeutic group"),use_container_width=True)

with tab2:
    st.info("A valid price-gap comparison requires the same composition, comparable pack/unit size, and comparable collection dates. The seed generic catalogue is historical (2018), so it is not presented as a current market gap.")
    if not brand.empty:
        match_terms={"Metformin 500mg":"Metformin 500mg","Atorvastatin 10mg":"Atorvastatin 10mg","Paracetamol 500mg":"Paracetamol 500mg"}
        # Display branded distributions only; current PMBI export will enable exact matching after refresh.
        for k in match_terms:
            x=brand[brand.active_salt_composition.str.contains(k.split()[0],case=False,na=False)]
            if not x.empty:
                st.write(k)
                st.dataframe(x[["branded_name","manufacturer","packaging","mrp_inr","source_url"]],use_container_width=True)

with tab3:
    st.subheader("Branded source records")
    st.dataframe(brand,use_container_width=True)
    st.subheader("Government generic source records")
    st.dataframe(gen,use_container_width=True)

st.sidebar.header("Filters")
if not brand.empty:
    manufacturers=st.sidebar.multiselect("Manufacturer",sorted(brand["manufacturer"].dropna().unique()))
    if manufacturers:
        st.dataframe(brand[brand["manufacturer"].isin(manufacturers)],use_container_width=True)
