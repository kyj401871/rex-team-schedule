import streamlit as st
import pandas as pd
import os
import sys # sys 모듈 추가
import uuid
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ==========================================
# 🛠️ 경로 설정 (EXE 실행 시 데이터 보존을 위해 필수)
# ==========================================
if getattr(sys, 'frozen', False):
    # exe로 실행될 때: exe 파일이 있는 폴더 위치
    application_path = os.path.dirname(sys.executable)
else:
    # 파이썬으로 실행될 때: 현재 파일 위치
    application_path = os.path.dirname(os.path.abspath(__file__))

# CSV 파일 경로를 절대 경로로 지정
CSV_FILE = os.path.join(application_path, 'tasks.csv')
# ==========================================

# 1. 기본 설정
st.set_page_config(page_title="팀 작업 관리자", layout="wide", initial_sidebar_state="expanded")

# 1. 기본 설정
st.set_page_config(page_title="팀 작업 관리자", layout="wide", initial_sidebar_state="expanded")
CSV_FILE = 'tasks.csv'

# 2. 데이터 관리 함수
def load_data():
    required_cols = ["ID", "작업내용", "담당자", "장소", "상태", "작성일"]
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=required_cols)
    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
        # 필수 컬럼 누락 방지
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        return df[required_cols]
    except:
        return pd.DataFrame(columns=required_cols)

def save_data(df):
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# 3. 세션 초기화 (데이터 로드)
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# ==========================================
# 🟢 사이드바: 새 작업 추가
# ==========================================
with st.sidebar:
    st.header("➕ 새 작업 추가")
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("작업 내용")
        assignee = st.text_input("담당자 이름")
        location = st.text_input("장소")
        status = st.selectbox("상태", ["대기중", "진행중", "완료", "보류"])
        submitted = st.form_submit_button("작업 추가", use_container_width=True)

        if submitted:
            if task_name:
                new_data = {
                    "ID": str(uuid.uuid4()),
                    "작업내용": task_name,
                    "담당자": assignee,
                    "장소": location,
                    "상태": status,
                    "작성일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(st.session_state.df)
                st.rerun()
            else:
                st.warning("작업 내용을 입력해주세요.")

# ==========================================
# 📊 메인 화면: 작업 보드
# ==========================================
st.title("📝 공용 팀 작업 관리 보드")
st.caption("💡 '작업 내용' 왼쪽의 **체크박스**를 선택한 후 삭제 버튼을 누르세요.")

# 데이터가 비어있을 경우 안내 문구 표시
if st.session_state.df.empty:
    st.info("현재 등록된 작업이 없습니다. 사이드바에서 새 작업을 추가해보세요!")
    # 테이블 구조는 보여주기 위해 빈 데이터프레임으로 설정 계속 진행
    display_df = st.session_state.df
else:
    display_df = st.session_state.df


# AgGrid 설정
gb = GridOptionsBuilder.from_dataframe(display_df)

# 1. 텍스트 필터 설정: '포함'만 남기기
text_filter_params = {
    'filterOptions': ['contains'],   # 오직 'contains' 옵션만 활성화
    'suppressAndOrCondition': True,  # AND/OR 조건 숨기기 (심플하게 한 줄만 입력)
    'debounceMs': 200                # 입력 후 0.2초 뒤 검색 (성능 최적화)
}

# 2. 기본 컬럼 설정 (필터 파라미터 적용)
gb.configure_default_column(
    resizable=True, 
    sortable=True, 
    editable=True, 
    filter=True,
    filterParams=text_filter_params  # 여기에 위에서 만든 설정 적용
)

gb.configure_column("ID", hide=True) # ID 숨김
gb.configure_column("작업내용", headerName="작업 내용", flex=2, 
                    checkboxSelection=True, headerCheckboxSelection=True)
gb.configure_column("담당자", headerName="담당자", flex=1)
gb.configure_column("장소", headerName="장소", flex=1)

# 상태 컬럼은 드롭다운 선택이지만, 필터는 텍스트 검색을 유지하거나 별도 설정 가능
gb.configure_column("상태", headerName="상태", flex=1,
                    cellEditor='agSelectCellEditor', 
                    cellEditorParams={'values': ["대기중", "진행중", "완료", "보류"]})
gb.configure_column("작성일", headerName="작성일", flex=1, editable=False)

# 3. 한글화 설정 (필요한 문구만 심플하게)
korean_locale = {
    "contains": "포함",       # Contains -> 포함
    "filterOoo": "검색...",   # 입력창 Placeholder
    "noRowsToShow": "표시할 데이터가 없습니다."
}
gb.configure_grid_options(localeText=korean_locale)

gb.configure_selection(selection_mode="multiple", use_checkbox=False)
gb.configure_pagination(paginationPageSize=10)
grid_options = gb.build()


# 테이블 그리기
grid_response = AgGrid(
    display_df,
    gridOptions=grid_options,
    height=400,
    width='100%',
    update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
    theme="alpine",
    key="main_grid" # 고정 키를 사용하여 리렌더링 방지
)

# ==========================================
# 🗑️ 삭제 버튼 및 로직
# ==========================================
st.write("")
col_btn1, _ = st.columns([1, 4])

with col_btn1:
    if st.button("🗑️ 선택된 작업 삭제", type="primary", use_container_width=True):
        selected_rows = grid_response.get('selected_rows')
        
        # 선택된 데이터가 있는지 확인 (AgGrid 버전에 따라 타입이 다를 수 있음)
        if selected_rows is not None:
            # 리스트나 데이터프레임 형태를 처리
            if isinstance(selected_rows, list):
                selected_df = pd.DataFrame(selected_rows)
            else:
                selected_df = selected_rows
            
            if not selected_df.empty:
                # ID를 기준으로 원본에서 삭제
                ids_to_delete = selected_df['ID'].astype(str).tolist()
                st.session_state.df = st.session_state.df[~st.session_state.df['ID'].astype(str).isin(ids_to_delete)]
                
                # 파일 저장 후 즉시 리렌더링
                save_data(st.session_state.df)
                st.toast("성공적으로 삭제되었습니다!")
                st.rerun() # 삭제 후 즉시 새로고침
            else:
                st.warning("삭제할 항목을 선택해주세요.")
        else:
            st.warning("삭제할 항목을 선택해주세요.")

# ==========================================
# ⚡ 셀 수정 시 자동 저장 (선택 사항)
# ==========================================
updated_grid_data = grid_response.get('data')
if updated_grid_data is not None:
    updated_df = pd.DataFrame(updated_grid_data)
    # 데이터가 있고, 행 개수가 같을 때만 수정 사항 반영 (삭제 시 오작동 방지)
    if not updated_df.empty and len(updated_df) == len(st.session_state.df):
        if not updated_df.equals(st.session_state.df):
            st.session_state.df = updated_df
            save_data(updated_df)

# ==========================================
# 📈 통계 하단바
# ==========================================
st.divider()
c1, c2, c3 = st.columns(3)
df_now = st.session_state.df
c1.metric("총 작업", len(df_now))
c2.metric("완료", len(df_now[df_now['상태']=='완료']))
c3.metric("진행중", len(df_now[df_now['상태']=='진행중']))