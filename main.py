```python
import streamlit as st
import pandas as pd
import altair as alt

# 데이터 불러오기
@st.cache_data
def load_data():
    return pd.read_csv("your_data.csv", encoding="cp949")

data = load_data()

# 기본 필터 설정값
default_quarter = ["전체"]
default_market = ["골목상권", "전통시장"]
default_top5 = data.groupby("업종")["분기매출액"].sum().nlargest(5).index.tolist()

# 사이드바 - 데이터 필터
st.sidebar.header("데이터 필터")

# 분기 선택
quarters = ["전체"] + sorted(data["분기"].unique().tolist())
selected_quarter = st.sidebar.multiselect("분기 선택", quarters, default=default_quarter)

# 상권유형 선택
market_types = sorted(data["상권유형"].unique().tolist())
selected_market = st.sidebar.multiselect("상권유형 선택", market_types, default=default_market)

# 업종 선택
industry_types = sorted(data["업종"].unique().tolist())
selected_industry = st.sidebar.multiselect("업종 선택", industry_types, default=default_top5)

# 필터링 로직
filtered_data = data.copy()
if "전체" not in selected_quarter:
    filtered_data = filtered_data[filtered_data["분기"].isin(selected_quarter)]
if selected_market:
    filtered_data = filtered_data[filtered_data["상권유형"].isin(selected_market)]
if selected_industry:
    filtered_data = filtered_data[filtered_data["업종"].isin(selected_industry)]

# 필터링된 데이터 건수
st.sidebar.markdown(f"**필터링된 데이터: {len(filtered_data):,}건**")

# 데이터 다운로드 버튼
csv = filtered_data.to_csv(index=False, encoding="cp949")
st.sidebar.download_button(
    label="데이터 다운로드 (CSV)",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv"
)

# 필터 초기화 버튼
if st.sidebar.button("필터 초기화"):
    st.session_state.clear()
    st.experimental_rerun()

# 데이터 출처 표시
st.sidebar.markdown(
    "<sub>* 데이터 출처: [서울 열린데이터광장](https://data.seoul.go.kr/)</sub>",
    unsafe_allow_html=True
)

# 탭 생성
tab1, tab2 = st.tabs(["📊 매출 현황", "👥 고객 분석"])

with tab1:
    # KPI 계산
    total_sales = filtered_data["분기매출액"].sum() / 1e8
    total_transactions = filtered_data["분기거래건수"].sum() / 1e4
    unique_markets = filtered_data["상권이름"].nunique()
    unique_industries = filtered_data["업종"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 총 분기 매출액", f"{total_sales:,.1f} 억원")
    col2.metric("🛒 총 분기 거래건수", f"{total_transactions:,.1f} 만건")
    col3.metric("🏬 분석 상권 수", f"{unique_markets:,} 개")
    col4.metric("📂 업종 종류", f"{unique_industries:,} 개")

    # 업종별 매출 상위 10
    top10_industries = (
        filtered_data.groupby("업종")["분기매출액"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    top10_industries["억원"] = top10_industries["분기매출액"] / 1e8

    chart = (
        alt.Chart(top10_industries)
        .mark_bar()
        .encode(
            x=alt.X("억원:Q", title="매출액(억원)"),
            y=alt.Y("업종:N", sort="-x"),
            tooltip=["업종", "억원"]
        )
    )

    text = chart.mark_text(
        align="left", baseline="middle", dx=3
    ).encode(text=alt.Text("억원:Q", format=",.1f"))

    st.subheader("📌 분기 매출 TOP 10 업종")
    st.altair_chart(chart + text, use_container_width=True)

with tab2:
    # 성별 매출 도넛 차트
    gender_sales = filtered_data[["남성_매출_금액", "여성_매출_금액"]].sum().reset_index()
    gender_sales.columns = ["성별", "매출액"]
    gender_sales["성별"] = gender_sales["성별"].replace(
        {"남성_매출_금액": "남성", "여성_매출_금액": "여성"}
    )
    gender_chart = (
        alt.Chart(gender_sales)
        .mark_arc(innerRadius=60)
        .encode(theta="매출액", color="성별", tooltip=["성별", "매출액"])
    )
    st.subheader("⚧ 성별 매출 비율")
    st.altair_chart(gender_chart, use_container_width=True)

    # 연령대 매출 막대 차트
    age_cols = [
        "연령대_10_매출_금액",
        "연령대_20_매출_금액",
        "연령대_30_매출_금액",
        "연령대_40_매출_금액",
        "연령대_50_매출_금액",
        "연령대_60_이상_매출_금액",
    ]
    age_sales = filtered_data[age_cols].sum().reset_index()
    age_sales.columns = ["연령대", "매출액"]
    age_sales["연령대"] = age_sales["연령대"].str.replace("_매출_금액", "")
    age_chart = (
        alt.Chart(age_sales)
        .mark_bar()
        .encode(x="연령대", y="매출액", tooltip=["연령대", "매출액"])
    )
    st.subheader("👶🧑👵 연령대별 매출")
    st.altair_chart(age_chart, use_container_width=True)

# 푸터
st.markdown(
    "<hr><center>Made by 석리송, with AI support</center>",
    unsafe_allow_html=True
)
```
