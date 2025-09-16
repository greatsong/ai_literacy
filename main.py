import streamlit as st
import pandas as pd
import altair as alt

# 데이터 로드
@st.cache_data
def load_data():
    return pd.read_csv("your_data.csv", encoding="cp949")

data = load_data()

# 컬럼명 변경
rename_dict = {
    "상권_구분_코드_명": "상권유형",
    "상권_코드": "상권코드",
    "상권_코드_명": "상권이름",
    "서비스_업종_코드_명": "업종",
    "당월_매출_금액": "분기매출액",
    "당월_매출_건수": "분기거래건수"
}
data = data.rename(columns=rename_dict)

# 기본 필터 값 설정
default_quarters = ["전체"]
default_types = ["골목상권", "전통시장"]
top5_industries = (
    data.groupby("업종")["분기매출액"].sum().nlargest(5).index.tolist()
)

# 사이드바
st.sidebar.header("데이터 필터")

# 필터 - 분기
quarters = ["전체"] + sorted(data["기준_년_분기_코드"].unique().tolist())
selected_quarters = st.sidebar.multiselect("분기 선택", quarters, default=default_quarters)

# 필터 - 상권유형
types = sorted(data["상권유형"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect("상권유형 선택", types, default=default_types)

# 필터 - 업종
industries = sorted(data["업종"].dropna().unique().tolist())
selected_industries = st.sidebar.multiselect("업종 선택", industries, default=top5_industries)

# 필터 초기화 버튼
if st.sidebar.button("필터 초기화"):
    selected_quarters = default_quarters
    selected_types = default_types
    selected_industries = top5_industries

# 데이터 필터링
filtered_data = data.copy()
if "전체" not in selected_quarters:
    filtered_data = filtered_data[filtered_data["기준_년_분기_코드"].isin(selected_quarters)]
if selected_types:
    filtered_data = filtered_data[filtered_data["상권유형"].isin(selected_types)]
if selected_industries:
    filtered_data = filtered_data[filtered_data["업종"].isin(selected_industries)]

# 사이드바에 데이터 건수 표시
st.sidebar.markdown(f"**필터링된 데이터: {len(filtered_data):,}건**")

# 사이드바 데이터 다운로드
csv = filtered_data.to_csv(index=False, encoding="cp949")
st.sidebar.download_button(
    "데이터 다운로드 (CSV)",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv",
)

# 데이터 출처
st.sidebar.markdown(
    "<sub>*데이터 출처: [서울 열린데이터광장](https://data.seoul.go.kr/)</sub>",
    unsafe_allow_html=True
)

# 탭 생성
tab1, tab2 = st.tabs(["📊 매출 현황", "🧑‍🤝‍🧑 고객 분석"])

# 매출 현황 탭
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_sales = filtered_data["분기매출액"].sum() / 1e8
        st.metric("💰 총 분기 매출액", f"{total_sales:,.1f} 억원")
    with col2:
        total_trx = filtered_data["분기거래건수"].sum() / 1e4
        st.metric("🛒 총 분기 거래건수", f"{total_trx:,.1f} 만건")
    with col3:
        num_areas = filtered_data["상권이름"].nunique()
        st.metric("📍 분석 상권 수", f"{num_areas:,} 개")
    with col4:
        num_industries = filtered_data["업종"].nunique()
        st.metric("🏷️ 업종 종류", f"{num_industries:,} 개")

    st.subheader("📈 분기 매출 TOP 10 업종")
    top10_industries = (
        filtered_data.groupby("업종")["분기매출액"].sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    top10_industries["분기매출액_억"] = (top10_industries["분기매출액"] / 1e8).round(1)

    chart = (
        alt.Chart(top10_industries)
        .mark_bar(color="#4C78A8")
        .encode(
            x=alt.X("분기매출액_억:Q", title="매출액(억원)"),
            y=alt.Y("업종:N", sort="-x", title="업종"),
        )
    )
    text = chart.mark_text(
        align="left", baseline="middle", dx=3
    ).encode(text="분기매출액_억:Q")

    st.altair_chart(chart + text, use_container_width=True)

# 고객 분석 탭
with tab2:
    st.subheader("🧑‍🤝‍🧑 성별 매출 비중")
    gender_sales = {
        "남성": filtered_data["남성_매출_금액"].sum(),
        "여성": filtered_data["여성_매출_금액"].sum(),
    }
    gender_df = pd.DataFrame(list(gender_sales.items()), columns=["성별", "매출액"])

    gender_chart = (
        alt.Chart(gender_df)
        .mark_arc(innerRadius=50)
        .encode(
            theta="매출액:Q",
            color=alt.Color("성별:N", scale=alt.Scale(scheme="category10")),
            tooltip=["성별", "매출액"],
        )
    )
    st.altair_chart(gender_chart, use_container_width=True)

    st.subheader("📊 연령대별 매출 현황")
    age_cols = [
        "연령대_10_매출_금액", "연령대_20_매출_금액",
        "연령대_30_매출_금액", "연령대_40_매출_금액",
        "연령대_50_매출_금액", "연령대_60_이상_매출_금액"
    ]
    age_data = filtered_data[age_cols].sum().reset_index()
    age_data.columns = ["연령대", "매출액"]
    age_data["연령대"] = age_data["연령대"].str.replace("_매출_금액", "")

    age_chart = (
        alt.Chart(age_data)
        .mark_bar(color="#F28E2B")
        .encode(
            x=alt.X("연령대:N", sort=None, title="연령대"),
            y=alt.Y("매출액:Q", title="매출액"),
            tooltip=["연령대", "매출액"],
        )
    )
    st.altair_chart(age_chart, use_container_width=True)

# 페이지 하단 푸터
st.markdown(
    "<hr><center>Made by 석리송, with AI support</center>",
    unsafe_allow_html=True
)
