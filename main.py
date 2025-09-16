import streamlit as st
import pandas as pd

# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data
def load_data():
    # 같은 폴더에 있는 CSV 파일 불러오기 (cp949 인코딩)
    df = pd.read_csv("서울시 상권분석서비스(추정매출-상권)_2024년.csv", encoding="cp949")
    # 열 이름 변경
    rename_dict = {
        "상권_구분_코드_명": "상권유형",
        "상권_코드": "상권코드",
        "상권_코드_명": "상권이름",
        "서비스_업종_코드_명": "업종",
        "당월_매출_금액": "분기매출액",
        "당월_매출_건수": "분기거래건수",
    }
    df = df.rename(columns=rename_dict)
    return df

df = load_data()

# -----------------------------
# 제목
# -----------------------------
st.title("📊 서울시 상권 분석 대시보드")

# -----------------------------
# 필터 (분기 선택)
# -----------------------------
quarters = ["전체"] + sorted(df["기준_년분기_코드"].unique().tolist())
selected_quarter = st.selectbox("📅 분기를 선택하세요:", quarters)

# 선택된 분기 데이터 필터링
if selected_quarter != "전체":
    filtered_df = df[df["기준_년분기_코드"] == selected_quarter]
else:
    filtered_df = df.copy()

# -----------------------------
# 메트릭 계산
# -----------------------------
total_sales = filtered_df["분기매출액"].sum() / 1e8   # 억원 단위
total_transactions = filtered_df["분기거래건수"].sum() / 1e4  # 만 건 단위
unique_areas = filtered_df["상권이름"].nunique()
unique_categories = filtered_df["업종"].nunique()

# -----------------------------
# 화면 4칸 분할
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 총 분기 매출액", f"{total_sales:,.1f} 억원")

with col2:
    st.metric("🧾 총 분기 거래건수", f"{total_transactions:,.1f} 만 건")

with col3:
    st.metric("📍 분석 상권 수", f"{unique_areas:,} 개")

with col4:
    st.metric("🏷️ 업종 종류", f"{unique_categories:,} 개")
