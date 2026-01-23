import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일명
CSV_FILE = 'tasks.csv'

# 페이지 설정
st.set_page_config(page_title="팀 작업 관리자", layout="wide")

# 1. 데이터 불러오기 함수
def load_data():
    if not os.path.exists(CSV_FILE):
        # 파일이 없으면 기본 데이터프레임 생성
        df = pd.DataFrame(columns=["작업내용", "담당자", "날짜", "상태", "작성일"])
        return df
    
    # CSV 읽기
    df = pd.read_csv(CSV_FILE)
    
    # ★★★ [핵심 수정 부분] ★★★
    # 불러온 데이터의 '날짜'이 단순 글자(String)라면 날짜(Datetime) 형식으로 강제 변환합니다.
    # 그래야 st.data_editor의 달력 기능과 충돌하지 않습니다.
    if not df.empty and '날짜' in df.columns:
        df['날짜'] = pd.to_datetime(df['날짜'])
        
    return df

# 2. 데이터 저장하기 함수
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# 메인 타이틀
st.title("📝 공용 팀 작업 관리 보드")

# 사이드바: 새로운 작업 추가
with st.sidebar:
    st.header("새 작업 추가")
    with st.form("add_task_form"):
        task_name = st.text_input("작업 내용")
        assignee = st.text_input("담당자 이름")
        due_date = st.date_input("날짜")
        status = st.selectbox("상태", ["대기중", "진행중", "완료", "보류"])
        
        submitted = st.form_submit_button("작업 추가")
        
        if submitted and task_name and assignee:
            new_data = {
                "작업내용": task_name,
                "담당자": assignee,
                "날짜": pd.to_datetime(due_date), # 저장할 때도 날짜형식 유지
                "상태": status,
                "작성일": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            df = load_data()
            # 새로운 데이터를 DataFrame으로 만들어서 합치기
            new_row_df = pd.DataFrame([new_data])
            # 빈 데이터프레임일 경우 concat 경고 방지 등을 위해 데이터 타입 맞춤
            if not df.empty:
                new_row_df = new_row_df.astype(df.dtypes)
                
            new_df = pd.concat([df, new_row_df], ignore_index=True)
            save_data(new_df)
            st.success("작업이 추가되었습니다!")
            st.rerun() # 화면 새로고침

# 메인 화면: 작업 목록 표시 및 수정
st.subheader("📋 현재 작업 현황")
st.info("표 내용을 직접 수정하고 엔터를 치면 자동 저장됩니다. 행을 선택하고 Delete 키를 누르면 삭제됩니다.")

# 데이터 불러오기
df = load_data()

# 데이터 편집기 (여기서 상태 변경, 삭제 가능)
edited_df = st.data_editor(
    df,
    num_rows="dynamic", # 행 추가/삭제 가능
    use_container_width=True,
    key="data_editor", # 키 값을 주어 안정성 확보
    column_config={
        "상태": st.column_config.SelectboxColumn(
            "상태",
            help="작업 상태를 변경하세요",
            width="medium",
            options=["대기중", "진행중", "완료", "보류"],
            required=True,
        ),
        "날짜": st.column_config.DateColumn(
            "날짜",
            format="YYYY-MM-DD",
            step=1
        ),
    }
)

# 변경사항이 있으면 저장
# data_editor는 상호작용할 때마다 리런되므로, edited_df가 변경되면 바로 저장
if not df.equals(edited_df):
    save_data(edited_df)
    # st.toast("변경사항이 저장되었습니다!", icon="✅") # 너무 자주 뜨면 주석 처리

# 통계 대시보드 (간단한 시각화)
st.divider()
col1, col2, col3 = st.columns(3)

# 데이터가 비어있을 경우 에러 방지
if not edited_df.empty:
    with col1:
        st.metric("총 작업 수", len(edited_df))
    with col2:
        completed = len(edited_df[edited_df['상태'] == '완료'])
        st.metric("완료된 작업", completed)
    with col3:
        pending = len(edited_df[edited_df['상태'] == '진행중'])
        st.metric("진행 중인 작업", pending)
else:
    st.write("아직 데이터가 없습니다.")