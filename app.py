import streamlit as st
import pandas as pd
import os
import uuid  # ★ 고유 ID 생성을 위한 라이브러리 추가
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# 1. 설정
st.set_page_config(page_title="팀 작업 관리자", layout="wide", initial_sidebar_state="expanded")
CSV_FILE = 'tasks.csv'

# 2. 데이터 함수 (ID 관리 기능 추가)
def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=["ID", "작업내용", "담당자", "장소", "상태", "작성일"])
    try:
        df = pd.read_csv(CSV_FILE)
        # 필수 컬럼 확인
        required_cols = ["작업내용", "담당자", "장소", "상태", "작성일"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        
        # ★ 중요: ID 컬럼이 없으면 새로 만듭니다 (기존 데이터 호환)
        if "ID" not in df.columns:
            df["ID"] = [str(uuid.uuid4()) for _ in range(len(df))]
            
        return df
    except:
        return pd.DataFrame(columns=["ID", "작업내용", "담당자", "장소", "상태", "작성일"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# 3. 세션 초기화
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# ==========================================
# 🟢 사이드바
# ==========================================
with st.sidebar:
    st.header("➕ 새 작업 추가")
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("작업 내용")
        assignee = st.text_input("담당자 이름")
        location = st.text_input("장소")
        status = st.selectbox("상태", ["대기중", "진행중", "완료", "보류"])
        
        submitted = st.form_submit_button("작업 추가", use_container_width=True)

        if submitted:  # 내용이 비어있어도 추가 가능하게 변경 (필요시 task_name 조건 추가)
            new_data = {
                "ID": str(uuid.uuid4()), # ★ 고유 ID 생성
                "작업내용": task_name,
                "담당자": assignee,
                "장소": location,
                "상태": status,
                "작성일": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            new_row = pd.DataFrame([new_data])
            updated_df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            
            save_data(updated_df)
            st.session_state.df = updated_df
            st.rerun()

# ==========================================
# 📊 메인 화면
# ==========================================
st.title("📝 공용 팀 작업 관리 보드")
st.caption("💡 삭제할 행의 **체크박스**를 선택하고 아래 **빨간 삭제 버튼**을 누르세요.")

gb = GridOptionsBuilder.from_dataframe(st.session_state.df)

# 기본 설정 (엑셀 필터 포함)
gb.configure_default_column(
    resizable=True,
    sortable=True,
    editable=True,
    filter='agSetColumnFilter',
    filterParams={'buttons': ['reset', 'apply'], 'closeOnApply': True}
)

# 컬럼 설정
gb.configure_column("ID", hide=True) # ★ ID는 화면에 안 보이게 숨김
gb.configure_column("작업내용", headerName="작업 내용", flex=2)
gb.configure_column("담당자", headerName="담당자", flex=1)
gb.configure_column("장소", headerName="장소", flex=1)
gb.configure_column("상태", headerName="상태", flex=1,
                    cellEditor='agSelectCellEditor', 
                    cellEditorParams={'values': ["대기중", "진행중", "완료", "보류"]})
gb.configure_column("작성일", headerName="작성일", flex=1, editable=False)

# 체크박스
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gb.configure_pagination(paginationPageSize=10)
grid_options = gb.build()

grid_response = AgGrid(
    st.session_state.df,
    gridOptions=grid_options,
    height=400,
    width='100%',
    update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED, 
    data_return_mode="AS_INPUT",
    allow_unsafe_jscode=True,
    theme="alpine",
    reload_data=False,
    enable_enterprise_modules=True, 
    key="aggrid_main"
)