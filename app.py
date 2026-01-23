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
        df = pd.DataFrame(columns=["작업내용", "담당자", "장소", "마감일", "상태", "작성일"])
        return df
    
    df = pd.read_csv(CSV_FILE)
    
    # [안전한 처리] '장소' 컬럼이 없으면 추가
    if '장소' not in df.columns:
        df['장소'] = ""
    
    # 날짜 컬럼 변환 (없으면 무시)
    if not df.empty and '마감일' in df.columns:
        df['마감일'] = pd.to_datetime(df['마감일'], errors='coerce')
        
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
        location = st.text_input("장소")
        due_date = st.date_input("마감일")
        status = st.selectbox("상태", ["대기중", "진행중", "완료", "보류"])
        
        submitted = st.form_submit_button("작업 추가")
        
        if submitted and task_name and assignee:
            new_data = {
                "작업내용": task_name,
                "담당자": assignee,
                "장소": location,
                "마감일": pd.to_datetime(due_date),
                "상태": status,
                "작성일": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            df = load_data()
            
            # ★★★ [핵심 수정] ★★★
            # 기존 df가 비어 있거나 타입이 일치하지 않아도 자동으로 타입을 맞춰주는 방법
            new_row_df = pd.DataFrame([new_data])
            
            # df가 비어있으면, 그냥 new_row_df를 사용하고 저장
            if df.empty:
                new_df = new_row_df
            else:
                # 기존 df와 새 데이터를 합칠 때, 타입을 자동으로 맞춤 (astype 대신 concat 사용)
                new_df = pd.concat([df, new_row_df], ignore_index=True)
                
            save_data(new_df)
            st.success("작업이 추가되었습니다!")
            st.rerun()

# 메인 화면: 작업 목록 표시 및 수정
st.subheader("📋 현재 작업 현황")

df = load_data()

# 데이터 편집기
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor",
    column_config={
        "상태": st.column_config.SelectboxColumn(
            "상태",
            options=["대기중", "진행중", "완료", "보류"],
            required=True,
        ),
        "마감일": st.column_config.DateColumn("마감일", format="YYYY-MM-DD"),
        "장소": st.column_config.TextColumn("장소", help="작업 장소를 입력하세요"),
    }
)

if not df.equals(edited_df):
    save_data(edited_df)
    st.toast("변경사항이 저장되었습니다!", icon="✅")

# 통계 대시보드
st.divider()
if not edited_df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 작업 수", len(edited_df))
    with col2:
        completed = len(edited_df[edited_df['상태'] == '완료'])
        st.metric("완료된 작업", completed)
    with col3:
        pending = len(edited_df[edited_df['상태'] == '진행중'])
        st.metric("진행 중인 작업", pending)
else:
    st.write("아직 작업이 없습니다.")