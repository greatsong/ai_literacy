import streamlit as st
import pandas as pd
import altair as alt

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv", encoding="cp949")
    return df

data = load_data()

# 컬럼명 변경
data = data.rename(columns={
    "상권_구분_코드_명": "상권유형",
    "상권_코드": "상권코드",
    "상권_코드_명": "상권이름",
    "서비스_업종_코드_명": "업종",
    "당월_매출_금액": "분기매출액",
    "당월_매출_건수": "분기거래건수"
})

# 기본 필터값 설정
default_quarter = ["전체"]
default_type = ["골목상권", "전통시장"]
top5_industries = (
    data.groupby("업종")["분기매출액"].sum().nlargest(5).index.tolist()
)

# 사이드바
st.sidebar.header("데이터 필터")
quarters = ["전체"] + sorted(data["기준_년_분기_코드"].unique().tolist())
selected_quarters = st.sidebar.multiselect("분기 선택", quarters, default=default_quarter)

selected_types = st.sidebar.multiselect("상권유형", data["상권유형"].unique().tolist(), default=default_type)

selected_industries = st.sidebar.multiselect("업종", data["업종"].unique().tolist(), default=top5_industries)

# 필터 적용
filtered_data = data.copy()

if "전체" not in selected_quarters:
    filtered_data = filtered_data[filtered_data["기준_년_분기_코드"].isin(selected_quarters)]

if selected_types:
    filtered_data = filtered_data[filtered_data["상권유형"].isin(selected_types)]

if selected_industries:
    filtered_data = filtered_data[filtered_data["업종"].isin(selected_industries)]

# 필터링된 데이터 건수 표시
st.sidebar.markdown(f"**필터링된 데이터: {len(filtered_data):,}건**")

# 사이드바 버튼
csv = filtered_data.to_csv(index=False, encoding="cp949")
st.sidebar.download_button(
    label="데이터 다운로드 (CSV)",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv"
)

if st.sidebar.button("필터 초기화"):
    st.session_state["분기 선택"] = default_quarter
    st.session_state["상권유형"] = default_type
    st.session_state["업종"] = top5_industries
    st.rerun()

# 데이터 출처
st.sidebar.markdown(
    "<small>* 데이터 출처: [서울 열린데이터광장](https://data.seoul.go.kr/)</small>",
    unsafe_allow_html=True
)

# 탭 생성
tab1, tab2 = st.tabs(["📊 매출 현황", "👥 고객 분석"])

with tab1:
    # KPI
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_sales = filtered_data["분기매출액"].sum() / 1e8
        st.metric("💰 총 분기 매출액", f"{total_sales:,.1f} 억원")
    with col2:
        total_transactions = filtered_data["분기거래건수"].sum() / 1e4
        st.metric("🧾 총 분기 거래건수", f"{total_transactions:,.1f} 만건")
    with col3:
        unique_areas = filtered_data["상권이름"].nunique()
        st.metric("🏘️ 분석 상권 수", f"{unique_areas:,}")
    with col4:
        unique_industries = filtered_data["업종"].nunique()
        st.metric("🏷️ 업종 종류", f"{unique_industries:,}")

    # 업종별 매출 TOP 10
    st.subheader("🏆 분기 매출 TOP 10 업종")
    top10 = (
        filtered_data.groupby("업종")["분기매출액"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    top10["분기매출액_억원"] = (top10["분기매출액"] / 1e8).round(1)

    chart = (
        alt.Chart(top10)
        .mark_bar()
        .encode(
            x=alt.X("분기매출액_억원:Q", title="매출액 (억원)"),
            y=alt.Y("업종:N", sort="-x", title="업종"),
            tooltip=["업종", "분기매출액_억원"]
        )
    )

    text = (
        alt.Chart(top10)
        .mark_text(align="left", baseline="middle", dx=3)
        .encode(
            x="분기매출액_억원:Q",
            y="업종:N",
            text="분기매출액_억원:Q"
        )
    )

    st.altair_chart(chart + text, use_container_width=True)

with tab2:
    st.subheader("👫 성별 매출 비율")
    gender_sales = pd.DataFrame({
        "성별": ["남성", "여성"],
        "매출액": [
            filtered_data["남성_매출_금액"].sum(),
            filtered_data["여성_매출_금액"].sum()
        ]
    })
    gender_sales["매출액_억원"] = (gender_sales["매출액"] / 1e8).round(1)

    gender_chart = (
        alt.Chart(gender_sales)
        .mark_arc(innerRadius=60)
        .encode(
            theta="매출액_억원:Q",
            color="성별:N",
            tooltip=["성별", "매출액_억원"]
        )
    )
    st.altair_chart(gender_chart, use_container_width=True)

    st.subheader("📊 연령대별 매출")
    age_cols = [
        "연령대_10_매출_금액", "연령대_20_매출_금액",
        "연령대_30_매출_금액", "연령대_40_매출_금액",
        "연령대_50_매출_금액", "연령대_60_이상_매출_금액"
    ]
    age_sales = pd.DataFrame({
        "연령대": [col.replace("연령대_", "").replace("_매출_금액", "") for col in age_cols],
        "매출액": [filtered_data[col].sum() for col in age_cols]
    })
    age_sales["매출액_억원"] = (age_sales["매출액"] / 1e8).round(1)

    age_chart = (
        alt.Chart(age_sales)
        .mark_bar()
        .encode(
            x=alt.X("연령대:N", title="연령대"),
            y=alt.Y("매출액_억원:Q", title="매출액 (억원)"),
            tooltip=["연령대", "매출액_억원"]
        )
    )
    st.altair_chart(age_chart, use_container_width=True)

# 푸터
st.markdown("---")
st.markdown(
    "<p style='text-align: center;'>Made by 석리송, with AI support</p>",
    unsafe_allow_html=True
)
