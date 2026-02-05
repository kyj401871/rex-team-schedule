import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 기본 설정
# ==========================================
st.set_page_config(page_title="팀 작업 관리자", layout="wide")

# ==========================================
# 2. 데이터 관리 함수 (구글 시트 연동)
# ==========================================
def load_data():
    """구글 시트에서 데이터를 읽어옵니다."""
    # 캐시를 쓰지 않고(ttl=0) 매번 최신 데이터를 가져옵니다.
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        df = conn.read(ttl=0)
        
        # 필수 컬럼 정의
        required_cols = ["ID", "작업내용", "담당자", "장소", "상태", "작성일"]
        
        # 시트가 비어있거나 컬럼이 없으면 생성
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
                
        # 데이터가 없는 경우(NaN) 빈 문자열로 변환
        df = df.fillna("")
        
        # ID는 숫자가 아닌 문자열로 처리
        df['ID'] = df['ID'].astype(str)
        
        return df[required_cols]
        
    except Exception as e:
        # 에러 발생 시(시트가 비었거나 권한 문제 등) 빈 테이블 반환
        return pd.DataFrame(columns=["ID", "작업내용", "담당자", "장소", "상태", "작성일"])

def save_data(df):
    """구글 시트에 데이터를 덮어씁니다."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        conn.update(data=df)
        st.cache_data.clear() # 캐시 초기화
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다: {e}")

# ==========================================
# 3. 세션 초기화
# ==========================================
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 새로고침 버튼 (모바일에서 다른 사람이 쓴 글 확인용)
if st.button("🔄 최신 데이터 불러오기"):
    st.session_state.df = load_data()
    st.rerun()

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
                # 충돌 방지를 위해 저장 직전 최신 데이터 로드
                current_df = load_data()
                
                new_data = {
                    "ID": str(uuid.uuid4()),
                    "작업내용": task_name,
                    "담당자": assignee,
                    "장소": location,
                    "상태": status,
                    "작성일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                
                # 기존 데이터에 한 줄 추가 (concat 사용)
                updated_df = pd.concat([current_df, pd.DataFrame([new_data])], ignore_index=True)
                
                # 구글 시트에 저장
                save_data(updated_df)
                
                # 화면 갱신
                st.session_state.df = updated_df
                st.toast("✅ 작업이 추가되었습니다!")
                st.rerun()
            else:
                st.warning("작업 내용을 입력해주세요.")

# ==========================================
# 📊 메인 화면: 작업 보드
# ==========================================
st.title("📝 팀 작업 공유 보드")
st.caption("모바일에서도 실시간으로 공유됩니다. (구글 시트 연동됨)")

display_df = st.session_state.df

# AgGrid 옵션 설정
gb = GridOptionsBuilder.from_dataframe(display_df)

# 필터 및 기본 설정
gb.configure_default_column(
    resizable=True, 
    sortable=True, 
    editable=True, 
    filter=True,
    filterParams={'filterOptions': ['contains'], 'suppressAndOrCondition': True}
)

gb.configure_column("ID", hide=True)
gb.configure_column("작업내용", headerName="작업 내용", flex=2, checkboxSelection=True, headerCheckboxSelection=True)
gb.configure_column("담당자", headerName="담당자", flex=1)
gb.configure_column("장소", headerName="장소", flex=1)
gb.configure_column("상태", headerName="상태", flex=1, 
                    cellEditor='agSelectCellEditor', 
                    cellEditorParams={'values': ["대기중", "진행중", "완료", "보류"]})
gb.configure_column("작성일", headerName="작성일", flex=1, editable=False)

# 한글 설정
gb.configure_grid_options(localeText={"noRowsToShow": "표시할 데이터가 없습니다.", "contains": "포함", "filterOoo": "검색..."})
gb.configure_selection(selection_mode="multiple", use_checkbox=False)
gb.configure_pagination(paginationPageSize=10)

grid_options = gb.build()

# 테이블 표시
grid_response = AgGrid(
    display_df,
    gridOptions=grid_options,
    height=500,
    width='100%',
    update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
    theme="alpine",
    key="main_grid"
)

# ==========================================
# 🗑️ 삭제 버튼
# ==========================================
st.write("")
col_btn, _ = st.columns([1, 4])

with col_btn:
    if st.button("🗑️ 선택된 작업 삭제", type="primary", use_container_width=True):
        selected_rows = grid_response.get('selected_rows')
        
        if selected_rows is not None and len(selected_rows) > 0:
            # 리스트 처리
            if isinstance(selected_rows, list):
                selected_df = pd.DataFrame(selected_rows)
            else:
                selected_df = selected_rows
                
            # 실제 삭제 로직
            current_df = load_data() # 최신 데이터 기준
            ids_to_delete = selected_df['ID'].astype(str).tolist()
            
            # ID가 일치하지 않는 것만 남김 (삭제)
            final_df = current_df[~current_df['ID'].astype(str).isin(ids_to_delete)]
            
            save_data(final_df)
            st.session_state.df = final_df
            st.toast("🗑️ 삭제되었습니다!")
            st.rerun()
        else:
            st.warning("삭제할 항목을 먼저 선택해주세요.")

# ==========================================
# ⚡ 수정 사항 자동 저장 (셀 편집 시)
# ==========================================
updated_grid_data = grid_response.get('data')
if updated_grid_data is not None:
    updated_df = pd.DataFrame(updated_grid_data)
    
    # 데이터가 있고, 로컬 데이터와 달라졌을 때만 저장
    if not updated_df.empty and len(updated_df) == len(st.session_state.df):
        # 내용 비교 (문자열로 변환하여 비교)
        if not updated_df.astype(str).equals(st.session_state.df.astype(str)):
            save_data(updated_df)
            st.session_state.df = updated_df
            st.toast("💾 수정사항이 저장되었습니다.")

# ==========================================
# 📈 하단 통계
# ==========================================
st.divider()
c1, c2, c3 = st.columns(3)
if not display_df.empty:
    c1.metric("총 작업", len(display_df))
    c2.metric("완료된 작업", len(display_df[display_df['상태']=='완료']))
    c3.metric("진행중인 작업", len(display_df[display_df['상태']=='진행중']))