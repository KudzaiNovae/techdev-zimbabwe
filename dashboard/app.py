"""
TECHDEV-ZIMBABWE — Mapping Zimbabwe's Digital Deserts
A plain-language, presentation-style dashboard of Zimbabwe's connectivity gaps.

Run:
    pip install streamlit plotly
    streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Zimbabwe's Digital Deserts", page_icon="📶",
                   layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------- palette
NAVY="#1F4E79"; BLUE="#2563EB"; TEAL="#0E7490"; RED="#C00000"
AMBER="#F59E0B"; GREEN="#059669"; GREY="#94A3B8"; INK="#0F172A"; SLATE="#475569"

# ---------------------------------------------------------------- styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; }
.main .block-container { padding-top:1.2rem; max-width:1180px; }
#MainMenu, footer, header { visibility:hidden; }

.hero { background:linear-gradient(120deg,#1F4E79 0%,#163b5c 55%,#0E7490 100%);
        border-radius:18px; padding:2rem 2.2rem; color:#fff; margin-bottom:1.4rem; }
.hero h1 { font-size:2.1rem; font-weight:800; margin:0 0 .4rem 0; line-height:1.1; }
.hero p  { font-size:1.05rem; opacity:.92; margin:0; max-width:760px; }

.ptitle { font-size:1.55rem; font-weight:800; color:#0F172A; margin:.2rem 0 .15rem; }
.psub   { font-size:1rem; color:#64748B; margin-bottom:1.1rem; }
.shead  { font-size:1.12rem; font-weight:700; color:#0F172A; margin:.4rem 0 .2rem; }

.card { background:#fff; border:1px solid #EEF2F7; border-radius:14px;
        padding:1.05rem 1.25rem; box-shadow:0 1px 4px rgba(15,23,42,.05);
        border-top:4px solid #1F4E79; height:100%; }
.card.red{border-top-color:#C00000;} .card.green{border-top-color:#059669;}
.card.amber{border-top-color:#F59E0B;} .card.grey{border-top-color:#94A3B8;}
.card .lab{font-size:.72rem;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}
.card .val{font-size:1.95rem;font-weight:800;color:#0F172A;line-height:1.05;margin-top:.15rem;}
.card .val.red{color:#C00000;} .card .val.green{color:#059669;}
.card .sub{font-size:.82rem;color:#94A3B8;margin-top:.25rem;}

.note{border-radius:12px;padding:1rem 1.2rem;font-size:.95rem;margin:.6rem 0 1rem;line-height:1.5;}
.note.blue {background:#EFF6FF;border-left:4px solid #2563EB;color:#1E3A5F;}
.note.red  {background:#FEF2F2;border-left:4px solid #C00000;color:#7F1D1D;}
.note.green{background:#ECFDF5;border-left:4px solid #059669;color:#065F46;}
.note.amber{background:#FFFBEB;border-left:4px solid #F59E0B;color:#92400E;}
.divider{border-top:1px solid #EEF2F7;margin:1.3rem 0;}
[data-testid="stSidebar"]{background:#0F172A;}
[data-testid="stSidebar"] *{color:#CBD5E1 !important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#F8FAFC !important;}
.stTabs [data-baseweb="tab"]{border-radius:8px 8px 0 0;padding:.45rem 1.1rem;font-weight:600;}
small.cap{color:#94A3B8;font-size:.82rem;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- data
@st.cache_data
def load_data():
    base = Path(__file__).parent.parent
    files = {
        'ddi':'data/processed/ddi_country.csv',
        'districts':'data/processed/zwe_districts_ddi_census.csv',
        'coverage':'data/processed/potraz_q4_2025_coverage.csv',
        'stations':'data/processed/potraz_q4_2025_base_stations_by_area.csv',
        'afford':'data/processed/itu_affordability_sadc.csv',
        'headlines':'data/processed/potraz_q4_2025_headlines.csv',
        'sens':'data/processed/ddi_sensitivity.csv',
        'tech':'data/processed/potraz_q4_2025_internet_tech.csv',
        'subs':'data/processed/potraz_q4_2025_subscriptions.csv',
        'usage':'data/processed/potraz_q4_2025_data_usage.csv',
    }
    return {k:pd.read_csv(base/v) for k,v in files.items() if (base/v).exists()}

D = load_data()

# ---------------------------------------------------------------- helpers
def card(label, value, sub="", style=""):
    st.markdown(f"""<div class="card {style}"><div class="lab">{label}</div>
        <div class="val {style}">{value}</div><div class="sub">{sub}</div></div>""",
        unsafe_allow_html=True)

def note(text, kind="blue"):
    st.markdown(f'<div class="note {kind}">{text}</div>', unsafe_allow_html=True)

def title(t, sub=""):
    st.markdown(f'<div class="ptitle">{t}</div>', unsafe_allow_html=True)
    if sub: st.markdown(f'<div class="psub">{sub}</div>', unsafe_allow_html=True)

def styled(fig, height=380, t="", yt="", xt="", legend=True, ylim=None, xlim=None):
    fig.update_layout(font=dict(family="Inter,sans-serif", size=13, color=SLATE),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=55, r=22, t=52 if t else 14, b=64 if legend else 40), height=height,
        title=dict(text=t, font=dict(size=15.5, color=INK), x=0, xanchor="left"),
        showlegend=legend, bargap=0.3,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, x=0, font=dict(size=12)))
    fig.update_xaxes(showgrid=False, title_text=xt, color="#64748B", tickfont=dict(size=12))
    fig.update_yaxes(showgrid=True, gridcolor="#EEF2F7", title_text=yt, color="#64748B", tickfont=dict(size=12))
    if ylim: fig.update_yaxes(range=ylim)
    if xlim: fig.update_xaxes(range=xlim)
    return fig

def chart(fig): st.plotly_chart(fig, use_container_width=True)

# plain-language names for the four pillars
PILL = [("coverage_gap","No 4G signal",NAVY),
        ("adoption_gap","Not online yet",TEAL),
        ("affordability_gap","Data too costly",RED),
        ("electricity_gap","No power for towers",AMBER)]
PILL_C = {"coverage_gap_score":("No 4G signal",NAVY),"adoption_gap_score":("Not online yet",TEAL),
          "affordability_gap_score":("Data too costly",RED),"electricity_gap_score":("No power for towers",AMBER)}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("## 📶 Digital Deserts")
    st.caption("Mapping Zimbabwe's connectivity gaps · ITU Data Hackathon 2026")
    st.markdown("---")
    PAGES = ["🏠 The big picture","🌍 Zimbabwe vs neighbours","🏙️ Town vs countryside",
             "📡 Where the signal reaches","💸 The cost of getting online","🗼 Where the towers are",
             "🧮 How we measured it","✅ What should happen"]
    page = st.radio("Navigation", PAGES, label_visibility="collapsed")
    st.markdown("---")
    st.caption("**Team TECHDEV-ZIMBABWE**")
    st.caption("Kudzai Zhuwaki · Dorothy Matembudze")
    st.caption("Shannon Sikadi · Daniel Nkosana Mlandu")
    st.markdown("---")
    st.caption("Sources: ITU DataHub · POTRAZ Q4 2025 · World Bank · ZimStat 2022 Census · OpenCellID")

# ================================================================ PAGES
# ---------------------------------------------------------------- 1. Big picture
if page == PAGES[0]:
    st.markdown("""<div class="hero"><h1>Zimbabwe looks connected on paper.<br>Millions are still offline.</h1>
        <p>Official numbers say 8 in 10 Zimbabweans are connected. Look closer and the picture splits in two —
        a country of well-served cities and a countryside where the signal, the power, and affordable data run out.</p></div>""",
        unsafe_allow_html=True)

    c = st.columns(4)
    with c[0]: card("Say they're connected","84.6%","POTRAZ — mobile subscriptions")
    with c[1]: card("Actually use the internet","41.6%","World Bank — real users","red")
    with c[2]: card("Rural areas with 4G","29%","vs 96% in towns","red")
    with c[3]: card("Zimbabwe's regional rank","#4 of 6","on digital exclusion (SADC)","amber")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    a,b = st.columns([1.05,1])
    with a:
        st.markdown('<div class="shead">The headline hides the truth</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["On paper<br>(subscriptions)","In reality<br>(actual users)"],
            y=[84.6,41.6], marker_color=[GREY,RED], width=.55,
            text=["84.6%","41.6%"], textposition="outside", textfont=dict(size=18,color=INK)))
        chart(styled(fig, height=340, t="Connected on paper vs really online", yt="% of people", legend=False, ylim=[0,100]))
        note("A SIM card is not the same as being online. Many people own several SIMs, and a subscription "
             "doesn't mean someone can actually use the internet. The real gap is about <b>43 points</b>.","blue")
    with b:
        st.markdown('<div class="shead">Where the people are</div>', unsafe_allow_html=True)
        if 'districts' in D:
            df = D['districts']; u=df[df.urban_rural=='urban'].population.sum(); r=df[df.urban_rural=='rural'].population.sum()
            fig = go.Figure(go.Pie(labels=["Towns / cities","Countryside"], values=[u,r], hole=.55,
                marker_colors=[NAVY,RED], textinfo="label+percent", sort=False))
            fig.add_annotation(text=f"<b>15.2M</b><br>people", showarrow=False, font=dict(size=15,color=INK))
            chart(styled(fig, height=340, t="Zimbabwe's population (2022 Census)", legend=False))
        note("About <b>7 in 10</b> Zimbabweans live in the countryside — exactly where coverage, "
             "power and affordable data are weakest.","amber")

# ---------------------------------------------------------------- 2. SADC
elif page == PAGES[1]:
    title("How Zimbabwe compares to its neighbours",
          "We scored six Southern African countries on digital exclusion. 0 = fully connected, 100 = totally cut off.")
    if 'ddi' in D:
        d = D['ddi'].sort_values('ddi')
        fig = go.Figure(go.Bar(x=d.ddi, y=d.country_name, orientation='h',
            marker_color=[RED if n=='Zimbabwe' else NAVY for n in d.country_name],
            text=[f"{v:.0f}" for v in d.ddi], textposition="outside", textfont=dict(size=15,color=INK)))
        chart(styled(fig, height=360, t="Digital exclusion score (higher = worse)", xt="Score 0–100", legend=False, xlim=[0,80]))
        note("Zimbabwe sits <b>4th of 6</b> — middle of the pack. Malawi and Mozambique fare worse mainly "
             "because almost nobody is online and rural areas have no power. Botswana and South Africa do best.","blue")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="shead">What\'s holding each country back?</div>', unsafe_allow_html=True)
        ds = D['ddi'].sort_values('ddi', ascending=False)
        fig = go.Figure()
        for col,(lab,clr) in PILL_C.items():
            fig.add_trace(go.Bar(name=lab, x=ds.country_name, y=ds[col], marker_color=clr))
        chart(styled(fig, height=420, t="The four things we measured, by country", yt="Score (higher = worse)"))
        cc = st.columns(2)
        with cc[0]:
            note("<b>Zimbabwe's signature problem is the signal.</b> Its <i>No 4G signal</i> score (44) is the "
                 "worst in the group — the others all have 85%+ 4G reach. Coverage, not price, is the first thing to fix.","red")
        with cc[1]:
            note("<b>But getting people online matters just as much.</b> Zimbabwe's <i>Not online yet</i> score (58) "
                 "is even higher than its signal gap — so towers alone won't close the divide.","amber")

# ---------------------------------------------------------------- 3. Town vs countryside
elif page == PAGES[2]:
    title("Town vs countryside",
          "Coverage, power and data prices are reported as town-vs-countryside averages — so a district's "
          "score reflects whether it's urban or rural. It is not yet a per-district measurement.")
    if 'districts' in D:
        df = D['districts']; u=df[df.urban_rural=='urban']; r=df[df.urban_rural=='rural']
        c = st.columns(3)
        with c[0]: card("Towns / cities",f"{len(u)} areas",f"{u.population.sum()/df.population.sum()*100:.0f}% of people")
        with c[1]: card("Countryside",f"{len(r)} areas",f"{r.population.sum()/df.population.sum()*100:.0f}% of people","red")
        with c[2]: card("Exclusion score gap","27 → 52","town vs countryside","amber")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        a,b = st.columns([1.2,1])
        with a:
            pillars=[("Overall score","ddi"),("No 4G signal","coverage_gap"),("Not online","adoption_gap"),
                     ("Data cost","affordability_gap"),("No power","electricity_gap")]
            labs=[p[0] for p in pillars]
            uv=[round(u[c2].mean(),1) for _,c2 in pillars]; rv=[round(r[c2].mean(),1) for _,c2 in pillars]
            fig=go.Figure()
            fig.add_trace(go.Bar(name="Towns",x=labs,y=uv,marker_color=NAVY,text=[f"{v:.0f}" for v in uv],textposition="outside"))
            fig.add_trace(go.Bar(name="Countryside",x=labs,y=rv,marker_color=RED,text=[f"{v:.0f}" for v in rv],textposition="outside"))
            chart(styled(fig, height=400, t="What separates town from countryside", yt="Score (higher = worse)", ylim=[0,110]))
            st.markdown('<small class="cap">The gap is almost entirely about the signal and electricity. '
                        'Data price and being online are national figures, so they\'re the same on both sides.</small>',
                        unsafe_allow_html=True)
        with b:
            st.markdown('<div class="shead">Look up a district</div>', unsafe_allow_html=True)
            sel = st.selectbox("Choose a district", sorted(df.district_name.unique()))
            row = df[df.district_name==sel].iloc[0]
            kind = row.urban_rural.title()
            card("Exclusion score", f"{row.ddi:.0f}",
                 f"{'Better connected' if row.ddi<40 else 'A digital desert'} · {kind} area",
                 "green" if row.ddi<40 else "red")
            st.write("")
            card("People (2022 Census)", f"{int(row.population):,}", f"{kind} district")
            st.write("")
            card("Has 4G signal", f"{row.pop_covered_4g_pct:.0f}%", f"Electricity: {row.electricity_access_pct:.0f}%","amber")
        note("Why only two levels? Because the inputs are town/countryside averages. A true district-by-district "
             "score would need more detailed data we don't have yet — for example the actual number of cell towers "
             "in each district.","blue")

# ---------------------------------------------------------------- 4. Coverage
elif page == PAGES[3]:
    title("Where the signal reaches",
          "96% of town-dwellers have 4G. Only 29% of rural Zimbabweans do. Newer 5G barely exists outside cities.")
    if 'coverage' in D:
        cov = D['coverage']
        fig=go.Figure()
        fig.add_trace(go.Bar(name="Towns",x=cov.technology,y=cov.pop_coverage_urban_pct,marker_color=NAVY,
            text=[f"{v:.0f}%" for v in cov.pop_coverage_urban_pct],textposition="outside"))
        fig.add_trace(go.Bar(name="Countryside",x=cov.technology,y=cov.pop_coverage_rural_pct,marker_color=RED,
            text=[f"{v:.0f}%" for v in cov.pop_coverage_rural_pct],textposition="outside"))
        chart(styled(fig, height=400, t="Share of people covered, by network type", yt="% of people covered", ylim=[0,115]))
        c=st.columns(3)
        with c[0]: card("4G gap, town vs country","67 points","96% vs 29%","red")
        with c[1]: card("5G in the countryside","0%","vs 19% in towns","red")
        with c[2]: card("Even basic 3G rural","74%","a quarter still on 2G only","amber")
        note("Most rural Zimbabweans can make a call (2G) but can't reliably do the modern things that matter — "
             "video lessons, telemedicine, online forms, mobile banking beyond simple USSD. That's the difference "
             "between <b>having a signal</b> and <b>having a useful signal</b>.","blue")

# ---------------------------------------------------------------- 5. Affordability
elif page == PAGES[4]:
    title("The cost of getting online",
          "Basic data is close to affordable. But the moment you need enough to study, work or see a doctor online, the price jumps.")
    if 'afford' in D:
        af = D['afford'].sort_values('basket_low_1gb_pct_gni', ascending=False)
        fig=go.Figure(go.Bar(x=af.country_name, y=af.basket_low_1gb_pct_gni,
            marker_color=[RED if i=='ZWE' else NAVY for i in af.country_iso3],
            text=[f"{v:.1f}%" for v in af.basket_low_1gb_pct_gni], textposition="outside", textfont=dict(size=14)))
        fig.add_hline(y=2, line_dash="dash", line_color=GREEN, line_width=2,
                      annotation_text="UN target: 2% of income", annotation_position="top right",
                      annotation_font_color=GREEN)
        chart(styled(fig, height=370, t="Cost of 1GB of data (share of monthly income)", yt="% of income", legend=False))
        note("For a basic 1GB, Zimbabwe (<b>3.15%</b>) is mid-range for the region — cheaper than Malawi or "
             "Mozambique. The problem isn't basic browsing; it's heavy use.","blue")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        a,b=st.columns([1,1])
        with a:
            st.markdown('<div class="shead">Cost climbs fast with real use</div>', unsafe_allow_html=True)
            zw = D['afford'][D['afford'].country_iso3=='ZWE'].iloc[0]
            labs=["Basic<br>1GB","Heavy<br>5GB mobile","Home<br>5GB fixed"]
            vals=[zw.basket_low_1gb_pct_gni, zw.basket_data_only_5gb_pct_gni, zw.basket_fixed_bb_5gb_pct_gni]
            fig=go.Figure(go.Bar(x=labs,y=vals,marker_color=[GREEN,RED,RED],
                text=[f"{v:.1f}%" for v in vals],textposition="outside",textfont=dict(size=15)))
            fig.add_hline(y=2,line_dash="dash",line_color=GREEN)
            chart(styled(fig, height=340, t="Zimbabwe: data cost by how much you need", yt="% of income", legend=False, ylim=[0,16]))
        with b:
            st.markdown('<div class="shead">What people spend their data on</div>', unsafe_allow_html=True)
            if 'usage' in D:
                us=D['usage']
                fig=go.Figure(go.Pie(labels=us.application, values=us.share_pct, hole=.5, sort=False,
                    marker_colors=[GREEN,RED,BLUE,AMBER,GREY], textinfo="label+percent"))
                chart(styled(fig, height=340, t="Share of mobile data traffic", legend=False))
        note("A student doing e-learning, a patient using telemedicine, or a remote worker needs 5GB or more — "
             "where the cost hits <b>6× the UN target</b>. In April 2026 the ICT Minister ordered POTRAZ to review "
             "these prices. People stretch what little data they have on WhatsApp.","amber")

# ---------------------------------------------------------------- 6. Infrastructure
elif page == PAGES[5]:
    title("Where the towers are",
          "Most of Zimbabwe's masts sit in towns. Satellite internet is now the fastest-growing way to fill the rural gap.")
    if 'stations' in D:
        bs = D['stations'][D['stations'].operator!='Total']
        fig=go.Figure()
        fig.add_trace(go.Bar(name="Town towers",x=bs.operator,y=bs.urban,marker_color=NAVY,
            text=bs.urban,textposition="outside"))
        fig.add_trace(go.Bar(name="Countryside towers",x=bs.operator,y=bs.rural,marker_color=RED,
            text=bs.rural,textposition="outside"))
        chart(styled(fig, height=370, t="Mobile towers by operator and area", yt="Number of towers"))
        c=st.columns(3)
        with c[0]: card("Towers in towns","8,423","64% of all towers")
        with c[1]: card("Towers in countryside","4,681","36% — for 70% of people","red")
        with c[2]: card("Biggest network","Econet","74% of mobile users")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    a,b=st.columns([1.1,1])
    with a:
        st.markdown('<div class="shead">Satellite is filling the gap</div>', unsafe_allow_html=True)
        if 'tech' in D:
            t = D['tech'][~D['tech'].technology.isin(['Total'])].sort_values('change_pct')
            fig=go.Figure(go.Bar(x=t.change_pct,y=t.technology,orientation='h',
                marker_color=[GREEN if v>0 else GREY for v in t.change_pct],
                text=[f"{v:+.0f}%" for v in t.change_pct],textposition="outside"))
            chart(styled(fig, height=360, t="Growth in internet connections (last quarter)", xt="Change %", legend=False))
        note("<b>Starlink (VSAT) grew 32% in a single quarter</b> — by far the fastest. For remote schools and "
             "clinics that no operator will ever reach commercially, satellite is becoming the practical answer.","green")
    with b:
        st.markdown('<div class="shead">Who provides mobile internet</div>', unsafe_allow_html=True)
        if 'subs' in D:
            sb=D['subs'][D['subs'].operator!='Total']
            fig=go.Figure(go.Pie(labels=sb.operator,values=sb.market_share_q4_pct,hole=.5,sort=False,
                marker_colors=[NAVY,BLUE,GREY],textinfo="label+percent"))
            chart(styled(fig, height=360, t="Mobile subscriber market share", legend=False))
        st.markdown('<small class="cap">A separate crowdsourced tower map (OpenCellID) backs this up but leans '
                    '99% toward one operator, so we use it only as a rough cross-check — never as exact counts.</small>',
                    unsafe_allow_html=True)

# ---------------------------------------------------------------- 7. Methodology
elif page == PAGES[6]:
    title("How we measured it",
          "One simple, honest score — built from public data anyone can re-check.")
    st.markdown('<div class="shead">The exclusion score adds up four things</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    items = [("📡 No 4G signal","Share of people <b>without</b> a 4G signal.",NAVY),
             ("🌐 Not online yet","Share of people <b>not</b> using the internet.",TEAL),
             ("💸 Data too costly","How expensive data is, vs people's income.",RED),
             ("🔌 No power for towers","Share of rural homes <b>without</b> electricity — a tower with no power is offline.",AMBER)]
    for col,(h,t,clr) in zip(cols,items):
        with col:
            st.markdown(f"""<div class="card" style="border-top-color:{clr}">
                <div class="val" style="font-size:1.05rem">{h}</div>
                <div class="sub" style="font-size:.86rem;color:#475569">{t}</div></div>""", unsafe_allow_html=True)
    note("We give all four equal weight, average them, and scale 0–100. No black boxes, no hidden tuning — "
         "run the same code on the same data and you get the same numbers.","blue")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="shead">Does the result hold up?</div>', unsafe_allow_html=True)
    if 'sens' in D:
        s=D['sens']
        fig=go.Figure(go.Bar(x=s.scheme,y=s.zwe_rank,marker_color=NAVY,
            text=[f"#{int(v)}" for v in s.zwe_rank],textposition="outside"))
        fig.update_yaxes(autorange="reversed", dtick=1)
        chart(styled(fig, height=330, t="Zimbabwe's rank when we change the recipe", yt="Rank (of 6)", legend=False))
        note("We re-ran the score six different ways — doubling the weight on coverage, on price, on adoption, "
             "even dropping electricity. Zimbabwe always lands <b>3rd or 4th of 6</b>. The conclusion doesn't depend "
             "on our choices.","green")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="shead">What we\'re honest about</div>', unsafe_allow_html=True)
    st.markdown("""
- **District scores are town-vs-countryside, not yet per-district** — coverage, power and price are only published as urban/rural averages.
- **District populations are real** 2022 Census figures, so the town/countryside split is solid.
- **Cross-country signal isn't perfectly like-for-like** — each country reports its own coverage; Zimbabwe's regulator reports rural coverage honestly (29%), so its rank is, if anything, conservative.
- **The score uses electricity as a stand-in for real network quality** — there's no measured-speed data yet.
""")

# ---------------------------------------------------------------- 8. Policy
elif page == PAGES[7]:
    title("What should happen",
          "Two facts drive everything: the signal is the first problem, and getting people online is the second.")
    note("<b>Build the towers — but don't stop there.</b> Zimbabwe has the region's weakest 4G reach, so "
         "infrastructure comes first. But more people are <i>offline</i> than are <i>uncovered</i>, so devices, "
         "affordable heavy-use data and digital skills have to go alongside.","blue")
    t1,t2,t3,t4 = st.tabs(["📡 Close the signal gap","💸 Make data affordable","🌐 Get people online","🔌 Power the towers"])
    with t1:
        st.markdown("""
**1. Target tower-building with the score.** 61 of the 91 districts are rural — use the exclusion score to decide where 4G goes, instead of leaving it to operators.

**2. Make operators share rural masts.** Towns have far denser coverage; sharing infrastructure cuts the cost of reaching the countryside.

**3. Lean on satellite for the hardest places.** Starlink grew 32% in one quarter — put it in remote schools and clinics now.

**4. Back community networks** where no operator will ever go commercially (Binga, Mbire, Tsholotsho).""")
    with t2:
        st.markdown("""
**5. Review prices on heavy-use data.** Basic 1GB is fine (3.15% of income); 5GB packages cost 6× the UN target. That's the minister's April 2026 directive — focus it there.

**6. Zero-rate the essentials** — education, health and farming services — in the worst-served districts.

**7. Tie spectrum fees to rural rollout.** Give operators a discount when they prove real 4G expansion in the neediest districts.""")
    with t3:
        st.markdown("""
**8. Tackle the phone gap.** Only ~15% own a smartphone. Device payment plans through mobile money would help.

**9. Teach digital skills,** not just literacy — many people who *could* get online still don't. Build it into the national AI strategy.

**10. Require quality reporting.** Operators should publish real speeds per area, so the score can one day measure quality, not just coverage.""")
    with t4:
        st.markdown("""
**11. Connect power and connectivity planning.** The districts without electricity (rural access 51% vs 84% in towns) are the same ones without signal. Co-fund solar-powered towers with the Rural Electrification Agency — one investment, two wins.""")
    note("The score isn't a one-off report. Re-run it each quarter with fresh POTRAZ data and you can track whether "
         "the gap is actually closing — district by district.","green")
