"""
TECHDEV-ZIMBABWE: Digital Desert Index Dashboard
Modern interactive explorer for Zimbabwe's connectivity gaps.

Run:
    pip install streamlit plotly
    streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --- Config ---
st.set_page_config(
    page_title="Zimbabwe Digital Desert Index",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Modern CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main .block-container { padding-top: 1.5rem; max-width: 1200px; }
    
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #1F4E79;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 0.8rem;
    }
    .metric-card.red { border-left-color: #C00000; }
    .metric-card.green { border-left-color: #059669; }
    .metric-card.grey { border-left-color: #6B7280; }
    .metric-label { font-size: 0.78rem; color: #6B7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.2rem; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1E293B; line-height: 1.1; }
    .metric-value.red { color: #C00000; }
    .metric-sub { font-size: 0.8rem; color: #94A3B8; margin-top: 0.2rem; }
    
    /* Page title */
    .page-title { font-size: 1.6rem; font-weight: 700; color: #1E293B; margin-bottom: 0.3rem; }
    .page-subtitle { font-size: 0.95rem; color: #64748B; margin-bottom: 1.5rem; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background: #0F172A; }
    [data-testid="stSidebar"] .css-1d391kg { padding-top: 1rem; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #CBD5E1 !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #F1F5F9 !important; }
    
    /* Divider */
    .section-divider { border-top: 1px solid #E2E8F0; margin: 1.5rem 0; }
    
    /* Insight box */
    .insight-box {
        background: #FEF2F2;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        border-left: 3px solid #C00000;
        font-size: 0.9rem;
        color: #7F1D1D;
        margin: 1rem 0;
    }
    .insight-box.blue {
        background: #EFF6FF;
        border-left-color: #1F4E79;
        color: #1E3A5F;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] { 
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.2rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

NAVY = "#1F4E79"
RED = "#C00000"
GREY = "#6B7280"
LIGHT = "#F1F5F9"

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", size=13),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#E2E8F0", gridwidth=0.5),
    yaxis=dict(gridcolor="#E2E8F0", gridwidth=0.5),
)

# --- Data loading ---
@st.cache_data
def load_data():
    base = Path(__file__).parent.parent
    data = {}
    files = {
        'ddi_country': 'data/processed/ddi_country.csv',
        'districts': 'data/processed/zwe_districts_ddi_census.csv',
        'coverage': 'data/processed/potraz_q4_2025_coverage.csv',
        'base_stations': 'data/processed/potraz_q4_2025_base_stations_by_area.csv',
        'affordability': 'data/processed/itu_affordability_sadc.csv',
        'zimstat': 'data/processed/zimstat_district_population.csv',
        'towers': 'data/processed/opencellid_district_towers.csv',
        'headlines': 'data/processed/potraz_q4_2025_headlines.csv',
        'sensitivity': 'data/processed/ddi_sensitivity.csv',
    }
    for key, path in files.items():
        p = base / path
        if p.exists():
            data[key] = pd.read_csv(p)
    return data

data = load_data()

def metric_card(label, value, sub="", style=""):
    return f"""<div class="metric-card {style}">
        <div class="metric-label">{label}</div>
        <div class="metric-value {style}">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>"""

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🌍 TECHDEV-ZIMBABWE")
    st.caption("ITU Data Hackathon 2026")
    st.markdown("---")
    
    page = st.radio("", [
        "Overview",
        "SADC Comparison",
        "District Explorer",
        "Coverage Gap",
        "Affordability",
        "Infrastructure",
        "Methodology",
        "Policy",
    ], label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("**Team**")
    st.caption("Kudzai Zhuwaki (Lead)")
    st.caption("Dorothy Matembudze")
    st.caption("Shannon Sikadi")
    st.caption("Daniel Nkosana Mlandu")
    st.markdown("---")
    st.caption("Data: ITU DataHub, World Bank, POTRAZ Q4 2025, ZimStat 2022 Census, OpenCellID")

# === PAGES ===

if page == "Overview":
    st.markdown('<div class="page-title">Mapping Zimbabwe\'s Digital Deserts</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Making digital exclusion visible, measurable, and actionable across 91 districts</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("POTRAZ Internet Penetration", "84.55%", "Q4 2025 headline figure"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Actually Using Internet", "41.6%", "World Bank 2024", "red"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Rural 4G Coverage", "29.0%", "vs 95.9% urban", "red"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Zimbabwe DDI", "45.7", "Rank 4 of 6 SADC peers"), unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### The 43-point gap")
        st.write("POTRAZ counts active data subscriptions. The World Bank counts people. Many Zimbabweans have multiple SIMs, and having a subscription is not the same as being meaningfully connected.")
        st.write("Behind the national averages lie deep digital deserts where coverage is absent, quality is poor, and data costs over 10% of monthly income.")
        
        st.markdown('<div class="insight-box">Zimbabwe faces two problems at once: a <b>supply gap</b> (worst 4G coverage in its SADC peer group) and a <b>demand gap</b> (adoption is even lower than coverage). Building towers is necessary but not sufficient. Closing the divide needs infrastructure <i>and</i> devices, affordability for heavy use, and digital literacy.</div>', unsafe_allow_html=True)

    with c2:
        if 'districts' in data:
            df = data['districts']
            u = df[df['urban_rural'] == 'urban']
            r = df[df['urban_rural'] == 'rural']
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Urban", x=["Population", "DDI Score"], 
                                y=[u['population'].sum(), u['ddi'].mean()],
                                marker_color=NAVY, text=[f"{u['population'].sum():,.0f}", f"{u['ddi'].mean():.1f}"],
                                textposition="outside"))
            fig.add_trace(go.Bar(name="Rural", x=["Population", "DDI Score"],
                                y=[r['population'].sum(), r['ddi'].mean()],
                                marker_color=RED, text=[f"{r['population'].sum():,.0f}", f"{r['ddi'].mean():.1f}"],
                                textposition="outside"))
            fig.update_layout(**PLOTLY_LAYOUT, barmode='group', 
                            title="Urban vs Rural: population and DDI",
                            showlegend=True, legend=dict(orientation="h", y=-0.15),
                            height=350)
            st.plotly_chart(fig, use_container_width=True)


elif page == "SADC Comparison":
    st.markdown('<div class="page-title">Digital Desert Index across SADC</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Zimbabwe ranks 4th of 6 peers. Coverage is the outlier.</div>', unsafe_allow_html=True)

    if 'ddi_country' in data:
        ddi = data['ddi_country'].sort_values('ddi', ascending=True)
        
        colors = [RED if n == 'Zimbabwe' else NAVY for n in ddi['country_name']]
        fig = go.Figure(go.Bar(
            x=ddi['ddi'], y=ddi['country_name'], orientation='h',
            marker_color=colors,
            text=ddi['ddi'].round(1), textposition='outside',
            textfont=dict(size=14, color="#1E293B"),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=350,
                         title="DDI Score (0-100, higher = more excluded)",
                         xaxis=dict(range=[0, 80], gridcolor="#E2E8F0"),
                         yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Pillar breakdown
        pillar_map = {'coverage_gap_score': 'Coverage', 'adoption_gap_score': 'Adoption',
                      'affordability_gap_score': 'Affordability', 'electricity_gap_score': 'Electricity'}
        pillar_cols = [c for c in ddi.columns if c in pillar_map]
        
        if pillar_cols:
            ddi_sorted = ddi.sort_values('ddi', ascending=False)
            fig2 = go.Figure()
            colors_pillar = [NAVY, "#4F81BD", RED, GREY]
            for i, col in enumerate(pillar_cols):
                fig2.add_trace(go.Bar(
                    name=pillar_map[col],
                    x=ddi_sorted['country_name'],
                    y=ddi_sorted[col],
                    marker_color=colors_pillar[i],
                ))
            fig2.update_layout(**PLOTLY_LAYOUT, barmode='group', height=400,
                             title="What drives each country's DDI",
                             yaxis_title="Pillar score (0-100)",
                             legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown('<div class="insight-box">Zimbabwe is a <b>coverage outlier</b>: its coverage gap (44.3) is 2.8x the next-worst country (Mozambique, 16.0). But its <b>adoption gap (58.4) is even higher than its coverage gap</b> — meaning more people are offline than are uncovered. Coverage is the binding supply constraint; adoption needs a parallel demand-side push.</div>', unsafe_allow_html=True)


elif page == "District Explorer":
    st.markdown('<div class="page-title">District-Level Digital Desert Index</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">91 districts from the ZimStat 2022 Census, classified by POTRAZ coverage data</div>', unsafe_allow_html=True)

    if 'districts' in data:
        df = data['districts']
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            selected = st.selectbox("Select a district", sorted(df['district_name'].dropna().unique()))
            
            if selected:
                row = df[df['district_name'] == selected].iloc[0]
                ur = row.get('urban_rural', '?')
                
                st.markdown(metric_card("DDI Score", f"{row['ddi']:.1f}", 
                    f"{'Better connected' if row['ddi'] < 40 else 'Digital desert'}", 
                    "green" if row['ddi'] < 40 else "red"), unsafe_allow_html=True)
                st.markdown(metric_card("Population", f"{int(row['population']):,}", 
                    f"{ur.title()} district"), unsafe_allow_html=True)
                st.markdown(metric_card("4G Coverage", f"{row.get('pop_covered_4g_pct', 'N/A')}%", 
                    "POTRAZ Q4 2025"), unsafe_allow_html=True)
                st.markdown(metric_card("Electricity", f"{row.get('electricity_access_pct', 'N/A')}%", 
                    "World Bank"), unsafe_allow_html=True)
                bs = row.get('base_stations_per_10k', 'N/A')
                st.markdown(metric_card("Towers per 10k", f"{bs}", 
                    "From POTRAZ base station allocation", "grey"), unsafe_allow_html=True)
        
        with c2:
            plot_df = df.sort_values('ddi', ascending=True)
            colors = [RED if ur == 'rural' else NAVY for ur in plot_df['urban_rural']]
            
            fig = go.Figure(go.Bar(
                x=plot_df['ddi'], y=plot_df['district_name'], orientation='h',
                marker_color=colors,
                customdata=plot_df[['population', 'urban_rural']],
                hovertemplate="<b>%{y}</b><br>DDI: %{x}<br>Pop: %{customdata[0]:,.0f}<br>%{customdata[1]}<extra></extra>",
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=max(500, len(plot_df) * 16),
                             title="All districts ranked by DDI",
                             xaxis_title="DDI (0-100)")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        u = df[df['urban_rural'] == 'urban']
        r = df[df['urban_rural'] == 'rural']
        with c1:
            st.markdown(metric_card("Urban districts", f"{len(u)}", f"{u['population'].sum():,.0f} people ({u['population'].sum()/df['population'].sum()*100:.0f}%)"), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card("Rural districts", f"{len(r)}", f"{r['population'].sum():,.0f} people ({r['population'].sum()/df['population'].sum()*100:.0f}%)", "red"), unsafe_allow_html=True)
        with c3:
            ratio = u['base_stations_per_10k'].mean() / r['base_stations_per_10k'].mean() if r['base_stations_per_10k'].mean() > 0 else 0
            st.markdown(metric_card("Tower density gap", f"{ratio:.1f}x", "Urban vs rural towers per 10k people", "grey"), unsafe_allow_html=True)


elif page == "Coverage Gap":
    st.markdown('<div class="page-title">The 67-point rural-urban 4G gap</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">95.9% of urban Zimbabweans have 4G. Only 29% of rural Zimbabweans do.</div>', unsafe_allow_html=True)

    if 'coverage' in data:
        cov = data['coverage']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Urban", x=cov['technology'], y=cov['pop_coverage_urban_pct'],
                            marker_color=NAVY, text=cov['pop_coverage_urban_pct'].apply(lambda x: f"{x}%"),
                            textposition='outside'))
        fig.add_trace(go.Bar(name="Rural", x=cov['technology'], y=cov['pop_coverage_rural_pct'],
                            marker_color=RED, text=cov['pop_coverage_rural_pct'].apply(lambda x: f"{x}%"),
                            textposition='outside'))
        fig.update_layout(**PLOTLY_LAYOUT, barmode='group', height=450,
                         title="Population coverage by technology (POTRAZ Q4 2025)",
                         yaxis_title="Coverage (%)", yaxis_range=[0, 115],
                         legend=dict(orientation="h", y=-0.12))
        
        fig.add_annotation(x="LTE", y=62, text="67-point gap", showarrow=True,
                          arrowhead=2, font=dict(size=15, color=RED, family="Inter"),
                          arrowcolor=RED)
        
        st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(metric_card("Urban base stations", "8,423", "64% of all towers"), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card("Rural base stations", "4,681", "36% of all towers", "red"), unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card("Rural 5G coverage", "0.0%", "vs 18.9% urban", "red"), unsafe_allow_html=True)

        st.markdown('<div class="insight-box">8,423 base stations serve urban areas (64% of total) while only 4,681 serve rural areas (36%) despite 60% of the population living rurally. OpenCellID independently confirms: of 8,587 crowdsourced towers, only 49 (0.6%) are LTE.</div>', unsafe_allow_html=True)


elif page == "Affordability":
    st.markdown('<div class="page-title">Affordability: close on basics, 6x on heavy use</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">The basic basket is near the UN target, but students and remote workers face much steeper costs</div>', unsafe_allow_html=True)

    if 'affordability' in data:
        aff = data['affordability'].sort_values('basket_low_1gb_pct_gni', ascending=False)
        
        fig = go.Figure()
        colors_bar = [RED if iso == 'ZWE' else NAVY for iso in aff['country_iso3']]
        fig.add_trace(go.Bar(
            x=aff['country_name'], y=aff['basket_low_1gb_pct_gni'],
            marker_color=colors_bar,
            text=aff['basket_low_1gb_pct_gni'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside', name="Low basket (1GB)"
        ))
        fig.add_hline(y=2, line_dash="dash", line_color="#059669", line_width=2,
                     annotation_text="UN 2% target", annotation_position="top left",
                     annotation_font_color="#059669")
        fig.update_layout(**PLOTLY_LAYOUT, height=400,
                         title="Mobile broadband basket (1GB) as % of GNI per capita",
                         yaxis_title="% of GNI", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        st.markdown("#### Zimbabwe basket comparison")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(metric_card("Basic 1GB", "3.15%", "UN target: 2%", "green"), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card("High 5GB", "9.05%", "4.5x the target", "red"), unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card("Data-only 5GB", "12.92%", "6.5x the target", "red"), unsafe_allow_html=True)
        with c4:
            st.markdown(metric_card("Fixed BB 5GB", "12.80%", "6.4x the target", "red"), unsafe_allow_html=True)

        st.markdown('<div class="insight-box blue">Basic mobile is mid-range in SADC (better than Malawi 7.7%). But students doing e-learning, patients using telemedicine, and remote workers need 5GB+, where costs hit 6x the UN target. In April 2026, Minister Mavetera ordered POTRAZ to conduct cost-based pricing reviews.</div>', unsafe_allow_html=True)


elif page == "Infrastructure":
    st.markdown('<div class="page-title">Infrastructure distribution</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Where the towers are vs where the people are</div>', unsafe_allow_html=True)

    if 'base_stations' in data:
        bs = data['base_stations']
        bs_ops = bs[bs['operator'] != 'Total']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Urban", x=bs_ops['operator'], y=bs_ops['urban'],
                            marker_color=NAVY, text=bs_ops['urban'], textposition='outside'))
        fig.add_trace(go.Bar(name="Rural", x=bs_ops['operator'], y=bs_ops['rural'],
                            marker_color=RED, text=bs_ops['rural'], textposition='outside'))
        fig.update_layout(**PLOTLY_LAYOUT, barmode='group', height=400,
                         title="Base stations by operator and area (POTRAZ Q4 2025)",
                         yaxis_title="Number of base stations",
                         legend=dict(orientation="h", y=-0.12))
        st.plotly_chart(fig, use_container_width=True)

    if 'towers' in data:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### OpenCellID crowdsourced tower density")
        
        tw = data['towers']
        if 'towers_per_10k' in tw.columns:
            tw_plot = tw.sort_values('towers_per_10k', ascending=True).tail(25)
            ur_colors = [RED if ur == 'rural' else NAVY for ur in tw_plot.get('urban_rural', ['rural']*len(tw_plot))]
            
            fig = go.Figure(go.Bar(
                x=tw_plot['towers_per_10k'], y=tw_plot['district_name'], orientation='h',
                marker_color=ur_colors,
                text=tw_plot['towers_per_10k'].apply(lambda x: f"{x:.1f}"),
                textposition='outside',
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=600,
                             title="Tower density by district (top 25)",
                             xaxis_title="Towers per 10k people")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="insight-box">OpenCellID data is crowdsourced and heavily biased toward NetOne (99% of entries). Use for relative density ranking between districts, not absolute tower counts.</div>', unsafe_allow_html=True)


elif page == "Methodology":
    st.markdown('<div class="page-title">Methodology and robustness</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">How the Digital Desert Index is built, and how sensitive the ranking is to our choices</div>', unsafe_allow_html=True)

    st.markdown("#### The four pillars")
    st.markdown("""
    The DDI is an equally-weighted mean of four sub-indices, each scaled 0-100 where higher means more excluded:
    """)
    
    method = pd.DataFrame([
        {"Pillar": "Coverage gap", "Formula": "100 − % population with 4G/LTE", "Source": "POTRAZ Q4 2025, ITU DataHub"},
        {"Pillar": "Adoption gap", "Formula": "100 − % individuals using Internet", "Source": "World Bank 2024"},
        {"Pillar": "Affordability gap", "Formula": "min(100, basket % of GNI × 10)", "Source": "ITU DataHub baskets"},
        {"Pillar": "Electricity gap", "Formula": "100 − % rural electricity access", "Source": "World Bank 2023"},
    ])
    st.dataframe(method, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### Sensitivity analysis: is the ranking robust?")
    st.write("A fair question for any composite index: does the result depend on the weights we chose? We re-ran the DDI under six weighting schemes. Zimbabwe stays between rank 3 and 4 of 6 in every case, never better than 3, never worse than 4.")

    if 'sensitivity' in data:
        sens = data['sensitivity']
        fig = go.Figure(go.Bar(
            x=sens['scheme'], y=sens['zwe_rank'],
            marker_color=NAVY,
            text=sens['zwe_rank'].apply(lambda x: f"#{int(x)}"),
            textposition='outside',
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=350,
                         title="Zimbabwe's DDI rank under different weighting schemes",
                         yaxis=dict(title="Rank (of 6)", autorange="reversed", dtick=1),
                         showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(sens, use_container_width=True, hide_index=True)

    st.markdown('<div class="insight-box blue">The ranking is robust. Whether we double the weight on coverage, affordability, adoption, or drop electricity entirely, Zimbabwe remains in the bottom half of the SADC peer group. The conclusion does not depend on our weighting choice.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### District refinement with OpenCellID")
    st.write("POTRAZ publishes coverage only at the national rural/urban level. To add genuine district-level variation, we blend OpenCellID crowdsourced tower density into each district's coverage pillar. Districts with above-median tower density per capita get a smaller coverage gap, and vice versa. This moves the district DDI from 2 possible values to 17 distinct scores.")

    st.markdown('<div class="insight-box">Caveat: OpenCellID is crowdsourced with a 99% NetOne bias, so we use it for relative ranking between districts, not absolute tower counts. The capped, median-normalised adjustment is deliberately conservative (±8 points maximum).</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### Known limitations")
    st.markdown("""
    - **ZimStat coverage is partial.** District population projections cover 42 districts across 4 provinces; the rest use census totals with area-based apportionment.
    - **Affordability uses national GNI**, not district income, so it understates barriers in poorer districts.
    - **No measured speed data.** Electricity access serves as a proxy for real-world network availability. A future quality pillar would use ITU QoS indicators or operator speed reports.
    - **POTRAZ coverage is operator-declared** and may overstate real-world signal.
    """)


elif page == "Policy":
    st.markdown('<div class="page-title">Policy recommendations</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">11 evidence-based recommendations grounded in DDI findings</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="insight-box">Two findings shape these recommendations: (1) Zimbabwe has the worst 4G coverage in its peer group, so <b>supply-side infrastructure</b> is the first-order fix, and (2) adoption lags even further behind coverage, so <b>demand-side measures</b> (devices, affordability, literacy) must run in parallel. Towers alone will not close the gap.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Coverage", "Affordability", "Adoption", "Electrification"])
    
    with tab1:
        st.markdown("#### Close the coverage gap (DDI 44.3 / worst in SADC)")
        st.markdown("""
        **1. Redirect the Universal Service Fund using the DDI as a targeting tool.**
        61 of 91 census districts are rural. Use the DDI to prioritise 4G tower deployment instead of operator-driven site selection.
        
        **2. Mandate shared rural infrastructure.**
        Tower density is 4.5x higher in urban areas. Require active network sharing in the worst-served districts to reduce per-operator deployment cost.
        
        **3. Accelerate Starlink at schools and clinics.**
        VSAT subscriptions grew 31.6% in Q4 2025 alone. Integrate satellite into the formal rural connectivity strategy.
        
        **4. Formalise community networks in coverage deserts.**
        In districts like Binga (159,982 people), Mbire (83,724), and Tsholotsho (115,782) where no operator will deploy commercially.
        """)
    
    with tab2:
        st.markdown("#### Improve affordability (DDI 31.5)")
        st.markdown("""
        **5. Cost-based pricing reviews on data-heavy baskets.**
        The basic 1GB basket (3.15% of GNI) is close to the UN 2% target. But data-only 5GB (12.92%) and fixed broadband (12.80%) are 6x over. Minister Mavetera's April 2026 directive is the policy hook.
        
        **6. Zero-rate education, health, and agriculture services.**
        Target bottom-quintile DDI districts specifically.
        
        **7. Link spectrum fees to rural deployment obligations.**
        Offer fee discounts conditioned on measurable 4G expansion in worst-served districts.
        """)
    
    with tab3:
        st.markdown("#### Enable adoption (DDI 58.4)")
        st.markdown("""
        **8. Address the device gap.**
        Smartphone penetration is around 15%. Explore device financing through mobile money instalment plans.
        
        **9. Invest in digital literacy via the AI Strategy 2026-2030.**
        Adult literacy is 93.2%, but digital literacy is a separate skill that requires structured programmes.
        
        **10. Mandate quality reporting.**
        POTRAZ currently reports coverage (yes/no) but not measured speed per ward. Require operators to publish median download speed and latency, enabling a future DDI quality pillar.
        """)
    
    with tab4:
        st.markdown("#### Electrification as connectivity enabler (DDI 48.6)")
        st.markdown("""
        **11. Co-locate connectivity and electrification investment.**
        Rural electricity access is 51.4% vs 84% urban. The same districts that lack power are the same districts that lack connectivity. Coordinate POTRAZ with the Rural Electrification Agency for solar-powered tower sites.
        """)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="insight-box blue">The DDI is not a one-time report. Re-running the pipeline with updated quarterly POTRAZ data measures progress. Every recommendation targets specific districts using the index.</div>', unsafe_allow_html=True)
