import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# 1. 기본 설정
st.set_page_config(page_title="팀 작업 관리자", layout="wide", initial_sidebar_state="expanded")
CSV_FILE = 'tasks.csv'

# 2. 데이터 함수
def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=["ID", "작업내용", "담당자", "장소", "상태", "작성일"])
    try:
        df = pd.read_csv(CSV_FILE)
        required_cols = ["작업내용", "담당자", "장소", "상태", "작성일"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        
        if "ID" not in df.columns:
            df["ID"] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        # ID를 맨 앞으로
        cols = ["ID"] + required_cols
        return df[cols]
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

        if submitted:
            new_data = {
                "ID": str(uuid.uuid4()),
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
st.caption("💡 '작업 내용' 왼쪽의 **체크박스**를 누르고 삭제 버튼을 사용하세요.")

gb = GridOptionsBuilder.from_dataframe(st.session_state.df)

# 기본 컬럼 설정 (엑셀 필터 적용)
gb.configure_default_column(
    resizable=True,
    sortable=True,
    editable=True,
    filter='agSetColumnFilter',
    filterParams={'buttons': ['reset', 'apply'], 'closeOnApply': True}
)

# 1. ID 컬럼 숨김
gb.configure_column("ID", hide=True)

# ★★★ [핵심 수정] 작업내용 컬럼에 체크박스 강제 부착 ★★★
gb.configure_column("작업내용", 
    headerName="작업 내용", 
    flex=2,
    checkboxSelection=True,        # 행마다 체크박스 표시
    headerCheckboxSelection=True,  # 헤더에 '전체 선택' 체크박스 표시
    headerCheckboxSelectionFilteredOnly=True # 필터링된 것만 전체선택
)

gb.configure_column("담당자", headerName="담당자", flex=1)
gb.configure_column("장소", headerName="장소", flex=1)
gb.configure_column("상태", headerName="상태", flex=1,
                    cellEditor='agSelectCellEditor', 
                    cellEditorParams={'values': ["대기중", "진행중", "완료", "보류"]})
gb.configure_column("작성일", headerName="작성일", flex=1, editable=False)

# 선택 모드 설정 (use_checkbox=False로 변경하여 중복 방지)
gb.configure_selection(selection_mode="multiple", use_checkbox=False)
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

# ==========================================
# 🗑️ 삭제 버튼
# ==========================================
st.write("")
col_btn1, col_btn2 = st.columns([1, 4])

with col_btn1:
    if st.button("🗑️ 선택된 작업 삭제", type="primary", use_container_width=True):
        selected = grid_response.get('selected_rows')
        
        if selected is None:
            selected_df = pd.DataFrame()
        elif isinstance(selected, pd.DataFrame):
            selected_df = selected
        else:
            selected_df = pd.DataFrame(selected)
            
        if not selected_df.empty:
            current_df = st.session_state.df
            
            # ID로 삭제
            if 'ID' in selected_df.columns:
                ids_to_delete = selected_df['ID'].tolist()
                current_df = current_df[~current_df['ID'].isin(ids_to_delete)]
                
                save_data(current_df)
                st.session_state.df = current_df
                st.toast("삭제되었습니다.", icon="🗑️")
                st.rerun()
            else:
                 # ID 로드 실패 시 백업 로직
                for index, row in selected_df.iterrows():
                     mask = (current_df['작업내용'] == row['작업내용']) & (current_df['작성일'] == row['작성일'])
                     current_df = current_df[~mask]
                save_data(current_df)
                st.session_state.df = current_df
                st.rerun()
        else:
            st.warning("먼저 표 안의 체크박스를 선택해주세요.")

# ==========================================
# ⚡ 데이터 자동 동기화
# ==========================================
raw_data = grid_response.get('data')

if isinstance(raw_data, pd.DataFrame):
    current_grid_df = raw_data
elif raw_data:
    current_grid_df = pd.DataFrame(raw_data)
else:
    current_grid_df = pd.DataFrame()

if not current_grid_df.empty:
    try:
        # ID 컬럼이 있는지 확인 후 비교
        cols_to_compare = [c for c in current_grid_df.columns if c != "ID"]
        
        # 간단 비교를 위해 내용만 체크
        if not current_grid_df.reset_index(drop=True).equals(st.session_state.df.reset_index(drop=True)):
            save_data(current_grid_df)
            st.session_state.df = current_grid_df
    except:
        pass

# ==========================================
# 📈 통계
# ==========================================
st.divider()
c1, c2, c3 = st.columns(3)
df_now = st.session_state.df
c1.metric("총 작업", len(df_now))
c2.metric("완료", len(df_now[df_now['상태']=='완료']))
c3.metric("진행중", len(df_now[df_now['상태']=='진행중']))