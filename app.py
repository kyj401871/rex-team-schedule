import streamlit as st
import pandas as pd
import os
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# 1. 설정
st.set_page_config(page_title="팀 작업 관리자", layout="wide", initial_sidebar_state="expanded")
CSV_FILE = 'tasks.csv'

# 2. 데이터 로드 함수
def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=["작업내용", "담당자", "장소", "상태", "작성일"])
    try:
        df = pd.read_csv(CSV_FILE)
        required_cols = ["작업내용", "담당자", "장소", "상태", "작성일"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        return df[required_cols]
    except:
        return pd.DataFrame(columns=["작업내용", "담당자", "장소", "상태", "작성일"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# 3. 세션 초기화
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# ==========================================
# 🟢 사이드바 (작업 추가)
# ==========================================
with st.sidebar:
    st.header("➕ 새 작업 추가")
    with st.form("add_task_form", clear_on_submit=True):
        task_name = st.text_input("작업 내용")
        assignee = st.text_input("담당자 이름")
        location = st.text_input("장소")
        status = st.selectbox("상태", ["대기중", "진행중", "완료", "보류"])

        submitted = st.form_submit_button("작업 추가", use_container_width=True)

        if submitted and task_name:
            new_data = {
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
# 📊 메인 화면 (필터 기능 추가)
# ==========================================
st.title("📝 공용 팀 작업 관리 보드")
st.caption("💡 각 컬럼의 **▼** 버튼을 클릭하면 엑셀과 같은 필터가 나타납니다.")

# AgGrid 설정
gb = GridOptionsBuilder.from_dataframe(st.session_state.df)

# ★★★ [필터 기능 추가] ★★★
# 모든 컬럼에 필터 활성화
gb.configure_column("작업내용", headerName="작업 내용", editable=True, flex=2, filter=True)
gb.configure_column("담당자", headerName="담당자", editable=True, flex=1, filter=True)
gb.configure_column("장소", headerName="장소", editable=True, flex=1, filter=True)

# 상태 컬럼: 드롭다운 필터 추가 (엑셀과 같은 UI)
gb.configure_column("상태",
    headerName="상태",
    editable=True,
    flex=1,
    cellEditor='agSelectCellEditor',
    cellEditorParams={'values': ["대기중", "진행중", "완료", "보류"]},
    filter=True,  # 필터 활성화
    filterParams={
        "suppressAndOrCondition": True,  # AND/OR 조건 숨기기
        "buttons": ["apply", "reset"],   # 적용/초기화 버튼 표시
        "closeOnApply": True             # 적용 후 필터 닫기
    }
)

gb.configure_column("작성일", headerName="작성일", flex=1, editable=False, filter=True)

# 체크박스 선택 기능
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gb.configure_pagination(paginationPageSize=10)

# ★★★ [한국어 로컬라이제이션] ★★★
locale_text = {
    "filterOparator": "필터 연산자",
    "andCondition": "AND",
    "orCondition": "OR",
    "applyFilter": "적용",
    "resetFilter": "초기화",
    "contains": "포함",
    "notContains": "미포함",
    "equals": "동일",
    "notEqual": "다름",
    "startsWith": "시작",
    "endsWith": "끝",
    "noRowsToShow": "표시할 데이터가 없습니다.",
    "selectAll": "(모두 선택)"
}

grid_options = gb.build()
grid_options["localeText"] = locale_text  # 한국어 적용

# AgGrid 출력
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
    key="aggrid_main"
)

# ==========================================
# 🗑️ 삭제 버튼
# ==========================================
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
            for index, row in selected_df.iterrows():
                mask = (current_df['작업내용'] == row['작업내용']) & \
                       (current_df['담당자'] == row['담당자']) & \
                       (current_df['작성일'] == row['작성일'])
                current_df = current_df[~mask]

            save_data(current_df)
            st.session_state.df = current_df
            st.toast("삭제되었습니다.", icon="🗑️")
            st.rerun()
        else:
            st.warning("삭제할 항목을 체크해주세요.")

# ==========================================
# 💾 자동 저장 (로딩 없이 즉시 반영)
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
        if not current_grid_df.reset_index(drop=True).equals(st.session_state.df.reset_index(drop=True)):
            save_data(current_grid_df)
            st.session_state.df = current_grid_df
    except:
        pass

# ==========================================
# 📈 통계 (필터링된 데이터 기준)
# ==========================================
st.divider()

# ★★★ [필터링된 데이터 가져오기] ★★★
filtered_data = grid_response['data']
if isinstance(filtered_data, pd.DataFrame):
    df_for_stats = filtered_data
else:
    df_for_stats = pd.DataFrame(filtered_data) if filtered_data else st.session_state.df

c1, c2, c3 = st.columns(3)
c1.metric("총 작업", len(df_for_stats))
c2.metric("완료", len(df_for_stats[df_for_stats['상태']=='완료']))
c3.metric("진행중", len(df_for_stats[df_for_stats['상태']=='진행중']))