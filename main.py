import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("서울시_상권분석서비스_샘플.csv", encoding="cp949")
    # 컬럼명 변경
    df = df.rename(columns={
        "상권_구분_코드_명": "상권유형",
        "상권_코드": "상권코드",
        "상권_코드_명": "상권이름",
        "서비스_업종_코드_명": "업종",
        "당월_매출_금액": "분기매출액",
        "당월_매출_건수": "분기거래건수"
    })
    return df

data = load_data()

# -----------------------------
# 사이드바 필터
# -----------------------------
st.sidebar.header("데이터 필터")

# 분기 필터
all_quarters = sorted(data["기준_년_코드"].astype(str) + "Q" + data["기준_분기_코드"].astype(str).unique())
selected_quarters = st.sidebar.multiselect(
    "분기 선택",
    options=["전체"] + all_quarters,
    default=["전체"]
)

# 상권유형 필터
unique_types = data["상권유형"].unique().tolist()
selected_types = st.sidebar.multiselect(
    "상권유형 선택",
    options=unique_types,
    default=["골목상권", "전통시장"] if "골목상권" in unique_types and "전통시장" in unique_types else unique_types
)

# 업종 필터 (매출 상위 5개 업종 기본값)
top5_industries = (
    data.groupby("업종")["분기매출액"].sum().sort_values(ascending=False).head(5).index.tolist()
)
unique_industries = data["업종"].unique().tolist()
selected_industries = st.sidebar.multiselect(
    "업종 선택",
    options=unique_industries,
    default=top5_industries
)

# -----------------------------
# 데이터 필터링
# -----------------------------
filtered_data = data.copy()

# 분기 필터 적용
if "전체" not in selected_quarters:
    split_quarters = [q.split("Q") for q in selected_quarters]
    mask = filtered_data.apply(
        lambda row: str(row["기준_년_코드"]) + "Q" + str(row["기준_분기_코드"]) in selected_quarters,
        axis=1
    )
    filtered_data = filtered_data[mask]

# 상권유형 필터 적용
if selected_types:
    filtered_data = filtered_data[filtered_data["상권유형"].isin(selected_types)]

# 업종 필터 적용
if selected_industries:
    filtered_data = filtered_data[filtered_data["업종"].isin(selected_industries)]

# -----------------------------
# 사이드바 추가 기능
# -----------------------------
# CSV 다운로드
csv_data = filtered_data.to_csv(index=False, encoding="cp949")
st.sidebar.download_button(
    label="📥 데이터 다운로드 (CSV)",
    data=csv_data,
    file_name="filtered_data.csv",
    mime="text/csv"
)

# 필터 초기화 (페이지 리로드 방식)
if st.sidebar.button("🔄 필터 초기화"):
    st.experimental_rerun()

# 데이터 출처
st.sidebar.markdown(
    "<small>* 데이터 출처: [서울 열린데이터광장](https://data.seoul.go.kr/)</small>",
    unsafe_allow_html=True
)

# -----------------------------
# 탭 구성
# -----------------------------
tab1, tab2 = st.tabs(["📊 매출 현황", "🧑‍🤝‍🧑 고객 분석"])

# -----------------------------
# 매출 현황 탭
# -----------------------------
with tab1:
    st.subheader("📊 매출 현황")

    # KPI 영역
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_sales = filtered_data["분기매출액"].sum() / 1e8  # 억원 단위
        st.metric("💰 총 분기 매출액", f"{total_sales:,.1f} 억원")
    with col2:
        total_txn = filtered_data["분기거래건수"].sum() / 1e4  # 만 건 단위
        st.metric("🧾 총 분기 거래건수", f"{total_txn:,.1f} 만 건")
    with col3:
        unique_markets = filtered_data["상권이름"].nunique()
        st.metric("🏬 분석 상권 수", f"{unique_markets:,} 개")
    with col4:
        unique_ind = filtered_data["업종"].nunique()
        st.metric("📂 업종 종류", f"{unique_ind:,} 개")

    # 업종별 매출 TOP 10
    st.markdown("### 🏆 분기 매출 TOP 10 업종")
    top10_sales = (
        filtered_data.groupby("업종")["분기매출액"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    top10_sales["억원"] = (top10_sales["분기매출액"] / 1e8).round(1)

    chart = (
        alt.Chart(top10_sales)
        .mark_bar()
        .encode(
            x=alt.X("억원:Q", title="매출액 (억원)"),
            y=alt.Y("업종:N", sort="-x", title="업종"),
            tooltip=["업종", "억원"]
        )
    )

    text = chart.mark_text(
        align="left",
        baseline="middle",
        dx=3
    ).encode(
        text="억원:Q"
    )

    st.altair_chart(chart + text, use_container_width=True)

# -----------------------------
# 고객 분석 탭
# -----------------------------
with tab2:
    st.subheader("🧑‍🤝‍🧑 고객 분석")

    # 성별 도넛 차트
    st.markdown("#### ⚧ 성별 매출 비중")
    gender_cols = ["남성_매출_금액", "여성_매출_금액"]
    gender_data = filtered_data[gender_cols].sum().reset_index()
    gender_data.columns = ["성별", "매출액"]
    gender_data["매출액억원"] = (gender_data["매출액"] / 1e8).round(1)

    donut = (
        alt.Chart(gender_data)
        .mark_arc(innerRadius=60)
        .encode(
            theta="매출액억원:Q",
            color="성별:N",
            tooltip=["성별", "매출액억원"]
        )
    )
    st.altair_chart(donut, use_container_width=True)

    # 연령대 매출 막대 차트
    st.markdown("#### 👥 연령대별 매출 현황")
    age_cols = [
        "연령대_10_매출_금액",
        "연령대_20_매출_금액",
        "연령대_30_매출_금액",
        "연령대_40_매출_금액",
        "연령대_50_매출_금액",
        "연령대_60_이상_매출_금액",
    ]
    age_data = filtered_data[age_cols].sum().reset_index()
    age_data.columns = ["연령대", "매출액"]
    age_data["매출액억원"] = (age_data["매출액"] / 1e8).round(1)

    bar = (
        alt.Chart(age_data)
        .mark_bar()
        .encode(
            x=alt.X("연령대:N", title="연령대"),
            y=alt.Y("매출액억원:Q", title="매출액 (억원)"),
            tooltip=["연령대", "매출액억원"]
        )
    )
    st.altair_chart(bar, use_container_width=True)

# -----------------------------
# 페이지 푸터
# -----------------------------
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Made by 석리송, with AI support</div>", unsafe_allow_html=True)

# -----------------------------
# 사이드바 데이터 건수 표시
# -----------------------------
st.sidebar.markdown(f"**필터링된 데이터: {len(filtered_data):,}건**")
