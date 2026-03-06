import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime, date
import io
import re

# ==========================================
# 1. 페이지 기본 설정 및 디자인
# ==========================================
st.set_page_config(page_title="Hollys QMS Premium", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Noto Sans KR', sans-serif; }
    .stApp { background-color: #F8F9FA; color: #212529; }
    .stButton>button { background-color: #D11031; color: white !important; border-radius: 8px; font-weight: 700; border: none; padding: 0.6rem 1.2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; }
    .stButton>button:hover { background-color: #A80D27; transform: translateY(-2px); }
    .metric-card { background-color: #FFFFFF; padding: 24px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 6px solid #D11031; margin-bottom: 20px; }
    .section-title { font-size: 1.2rem; font-weight: 700; color: #D11031; margin-top: 20px; border-bottom: 2px solid #D11031; padding-bottom: 5px; margin-bottom: 15px; }
    
    /* 📅 캘린더 상태 뱃지 스타일 */
    .badge { padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: bold; vertical-align: middle; display: inline-block; }
    .badge-upcoming { background-color: #E2F0FD; color: #0D6EFD; border: 1px solid #0D6EFD; }
    .badge-overdue { background-color: #FFF0F2; color: #D11031; border: 1px solid #D11031; }
    .badge-done { background-color: #E6F4EA; color: #28A745; border: 1px solid #28A745; }
    .badge-warning { background-color: #FFF3CD; color: #856404; border: 1px solid #856404; } 
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 로고 및 타이틀
# ==========================================
c_logo, c_title = st.columns([1, 5])
with c_logo:
    if os.path.exists("image_d70fe2.png"): st.image("image_d70fe2.png", width=120)
with c_title:
    st.title("Hollys Roasting Center QMS")
    st.markdown("<p style='color: #6C757D; font-size: 1.1rem; margin-top: -10px; margin-bottom: 20px;'>품질관리팀 전용 디지털 거버넌스 시스템</p>", unsafe_allow_html=True)

# ==========================================
# 3. 데이터베이스 로드 함수 및 상수
# ==========================================
DATA_FILE = "qc_data.csv"
SPEC_FILE = "qc_specs.csv"
CLEAN_FILE = "cleaning_specs.csv"
VERIFY_FILE = "verify_plan.csv"
OTHER_SCHED_FILE = "other_schedule.csv"
HEALTH_CERT_FILE = "health_cert.csv" 
EMPLOYEE_FILE = "employees.csv"
FACILITY_FILE = "facilities.csv"
REPAIR_FILE = "repairs.csv"
CALIB_LIST_FILE = "calib_list.csv"
CALIB_REPORT_FILE = "calib_report.csv"
FILTER_PLAN_FILE = "filter_plan.csv"

# 세척소독 대분류 11종
CLEAN_CATEGORIES = [
    "1. 종업원", "2. 위생복장", "3. 작업장 주변", "4. 작업장 내부(공통)", 
    "5. 식품 제조시설", "6. 보관시설", "7. 운반도구 및 용기", 
    "8. 모니터링 및 검사장비", "9. 환기시설", "10. 폐기물처리용기", "11. 세척 소독 도구"
]

def load_data():
    if os.path.exists(DATA_FILE): 
        try: return pd.read_csv(DATA_FILE)
        except: pass
    return pd.DataFrame(columns=["생산일", "유형", "제품명", "질소(%)", "수분(%)", "색도(Agtron)", "추출시간(sec)", "날짜기록", "판정", "비고"])

def load_specs():
    if os.path.exists(SPEC_FILE): 
        try:
            df = pd.read_csv(SPEC_FILE, dtype=str)
            if "제품코드" not in df.columns: df.insert(0, "제품코드", [f"P-{str(i+1).zfill(3)}" for i in range(len(df))])
            return df
        except: pass
    return pd.DataFrame(columns=["제품코드", "제품명", "유형", "최소_질소", "최대_질소", "최소_수분", "최대_수분", "최소_색도", "최대_색도", "최소_추출", "최대_추출", "날짜유형"])

def load_cleaning_specs():
    if os.path.exists(CLEAN_FILE): 
        try:
            df = pd.read_csv(CLEAN_FILE, dtype=str)
            req_cols = ['ID', '대분류', '구역', '설비명', '부위', '세척소독방법', '주기', '사용도구', '책임자', '사진파일']
            for col in req_cols:
                if col not in df.columns:
                    if col == 'ID': df['ID'] = [f"C-{str(i).zfill(4)}" for i in range(len(df))]
                    elif col == '대분류': df['대분류'] = "5. 식품 제조시설"  
                    elif col == '설비명': df['설비명'] = "기본대상"
                    elif col == '부위': df['부위'] = df.get('관리부위', "")
                    elif col == '세척소독방법': df['세척소독방법'] = df.get('작업방법', "")
                    elif col == '주기': df['주기'] = df.get('청소주기', "")
                    elif col == '사용도구': df['사용도구'] = df.get('세제_도구', "")
                    else: df[col] = ""
            return df[req_cols]
        except: pass
    df_clean = pd.DataFrame(columns=['ID', '대분류', '구역', '설비명', '부위', '세척소독방법', '주기', '사용도구', '책임자', '사진파일'])
    df_clean.to_csv(CLEAN_FILE, index=False, encoding='utf-8-sig')
    return df_clean

def load_filter_plan():
    if os.path.exists(FILTER_PLAN_FILE):
        try:
            df = pd.read_csv(FILTER_PLAN_FILE)
            # 과거 데이터 호환성 패치
            if '설비명_위치' in df.columns:
                df.rename(columns={'설비명_위치': '설치장소', '필터종류': '필터명', '최근점검일': '점검일자', '차기점검일': '차기점검일자'}, inplace=True)
                if '내용' not in df.columns: df['내용'] = '교체'
            if '설치장소' in df.columns: return df
        except: pass
    df_f = pd.DataFrame(columns=["설치장소", "필터명", "내용", "주기_개월", "점검일자", "차기점검일자", "상태", "비고"])
    df_f.to_csv(FILTER_PLAN_FILE, index=False, encoding='utf-8-sig')
    return df_f

def load_verify():
    if os.path.exists(VERIFY_FILE): 
        try: 
            df = pd.read_csv(VERIFY_FILE)
            if '계획일자' in df.columns: return df
        except: pass
    df_v = pd.DataFrame(columns=["계획일자", "검증종류", "검증항목", "세부내용", "검증방법", "상태"])
    df_v.to_csv(VERIFY_FILE, index=False, encoding='utf-8-sig')
    return df_v

def load_other_sched():
    if os.path.exists(OTHER_SCHED_FILE): 
        try:
            df = pd.read_csv(OTHER_SCHED_FILE)
            if '일자' in df.columns: return df
        except: pass
    df_o = pd.DataFrame(columns=["일자", "일정명", "세부내용", "상태"])
    df_o.to_csv(OTHER_SCHED_FILE, index=False, encoding='utf-8-sig')
    return df_o

def load_health_cert():
    if os.path.exists(HEALTH_CERT_FILE):
        try:
            df = pd.read_csv(HEALTH_CERT_FILE)
            if '검진일자' in df.columns: return df
        except: pass
    df_hc = pd.DataFrame(columns=["직급", "이름", "연락처", "검진일자"])
    df_hc.to_csv(HEALTH_CERT_FILE, index=False, encoding='utf-8-sig')
    return df_hc

def load_employees():
    if os.path.exists(EMPLOYEE_FILE):
        try:
            df = pd.read_csv(EMPLOYEE_FILE, dtype=str)
            if 'HACCP 직책' not in df.columns: df['HACCP 직책'] = "해당없음"
            if '모니터링 CCP' not in df.columns: df['모니터링 CCP'] = ""
            if '기타' not in df.columns: df['기타'] = ""
            if '사번' in df.columns: return df
        except: pass
    df_emp = pd.DataFrame(columns=["사번", "직급", "이름", "연락처", "입사일", "재직상태", "HACCP 직책", "모니터링 CCP", "기타"])
    df_emp.to_csv(EMPLOYEE_FILE, index=False, encoding='utf-8-sig')
    return df_emp

def load_facilities():
    if os.path.exists(FACILITY_FILE):
        try: return pd.read_csv(FACILITY_FILE, dtype=str)
        except: pass
    df = pd.DataFrame(columns=["설비번호", "설비명", "사용용도", "전압", "구입년월", "제조회사명", "설치장소", "관리부서", "관리자_정", "관리자_부", "특이사항"])
    df.to_csv(FACILITY_FILE, index=False, encoding='utf-8-sig')
    return df

def load_repairs():
    if os.path.exists(REPAIR_FILE):
        try: return pd.read_csv(REPAIR_FILE, dtype=str)
        except: pass
    df = pd.DataFrame(columns=["설비번호", "수리일자", "수리사항", "수리처", "비고"])
    df.to_csv(REPAIR_FILE, index=False, encoding='utf-8-sig')
    return df

def load_calib_list():
    if os.path.exists(CALIB_LIST_FILE):
        try: return pd.read_csv(CALIB_LIST_FILE, dtype=str)
        except: pass
    df = pd.DataFrame(columns=["관리번호", "검사_설비명", "측정범위", "주기", "구분", "검교정일자", "차기_검교정일자", "비고"])
    df.to_csv(CALIB_LIST_FILE, index=False, encoding='utf-8-sig')
    return df

def load_calib_reports():
    if os.path.exists(CALIB_REPORT_FILE):
        try: return pd.read_csv(CALIB_REPORT_FILE, dtype=str)
        except: pass
    df = pd.DataFrame(columns=["설비명", "교정일자", "작성자", "검교정방법", "판정기준", "표준값", "측정값", "보정율/오차", "개선조치", "판정결과"])
    df.to_csv(CALIB_REPORT_FILE, index=False, encoding='utf-8-sig')
    return df

def toggle_task_status(file_path, idx):
    try:
        temp_df = pd.read_csv(file_path)
        current_status = temp_df.loc[idx, '상태']
        temp_df.loc[idx, '상태'] = '예정' if current_status == '완료' else '완료'
        temp_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    except: pass

df = load_data()
df_specs = load_specs()
df_clean = load_cleaning_specs()

if 'selected_pcode' not in st.session_state:
    st.session_state.selected_pcode = None
    st.session_state.selected_pname = None
if 'is_edit_mode' not in st.session_state:
    st.session_state.is_edit_mode = False

# ==========================================
# 좌측 사이드바 메뉴 
# ==========================================
with st.sidebar:
    st.markdown("## 📋 메인 메뉴")
    
    menu_selection = st.radio(
        "이동할 메뉴를 선택하세요:",
        ["대시보드 (메인)", "캘린더", "현장 측정 기록", "데이터 히스토리", "제품 관리", "직원 관리", "설비 관리", "계측기기 검교정", "HACCP"]
    )
    
    sub_menu = None
    if menu_selection == "캘린더":
        st.divider()
        st.markdown("#### ↳ 캘린더 관리")
        sub_menu = st.radio("하위 메뉴 선택:", ["검증 계획표", "기타 일정"])
        
    elif menu_selection == "직원 관리":
        st.divider()
        st.markdown("#### ↳ 직원 관리 하위메뉴")
        sub_menu = st.radio("하위 메뉴 선택:", ["조직도 및 인원 관리", "보건증 현황관리"])
        
    elif menu_selection == "제품 관리":
        st.divider()
        st.markdown("#### ↳ 제품 관리 상세")
        sub_menu = st.radio("하위 메뉴 선택:", ["간편 판정 규격", "상세 규격서 마스터"])
        
    elif menu_selection == "설비 관리":
        st.divider()
        st.markdown("#### ↳ 설비 관리 하위메뉴")
        sub_menu = st.radio("하위 메뉴 선택:", ["제조위생설비이력관리", "필터 점검관리", "세척소독 기준"])
        
    elif menu_selection == "HACCP":
        st.divider()
        st.markdown("#### ↳ HACCP 관리")
        sub_menu = st.radio("하위 메뉴 선택:", ["HACCP 일지"])

st.divider()

# ==========================================
# 본문 렌더링
# ==========================================

# --- 1. 대시보드 (메인 화면) ---
if menu_selection == "대시보드 (메인)":
    
    c_left, c_right = st.columns([1, 1.2])
    
    with c_left:
        st.markdown('<div class="section-title">📊 종합 생산 및 품질 현황</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        pass_rate = 100
        if not df.empty and "판정" in df.columns: pass_rate = (len(df[df["판정"] == "PASS"]) / len(df)) * 100 if len(df) > 0 else 0
        col1.markdown(f'<div class="metric-card"><h4>총 생산 기록</h4><h2>{len(df)} 건</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><h4>종합 적합률</h4><h2>{pass_rate:.1f} %</h2></div>', unsafe_allow_html=True)
        
        if not df.empty and not df[df["질소(%)"] != "N/A"].empty:
            try:
                plot_df = df[df["질소(%)"] != "N/A"].copy()
                plot_df["질소(%)"] = pd.to_numeric(plot_df["질소(%)"], errors='coerce')
                plot_df = plot_df.dropna(subset=["질소(%)"])
                fig = px.line(plot_df.tail(15), x="생산일", y="질소(%)", color="제품명", markers=True, title="최근 질소 충진량 추이")
                fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("차트를 그리기 위한 유효한 품질 데이터가 부족합니다.")

    with c_right:
        st.markdown('<div class="section-title">📅 다가오는 캘린더 일정 (D-Day 연동)</div>', unsafe_allow_html=True)
        
        df_v = load_verify()
        df_o = load_other_sched()
        df_hc = load_health_cert()
        df_calib_c = load_calib_list()
        df_filter = load_filter_plan()
        
        agenda_list = []
        today_date = date.today()
        
        if not df_v.empty and '계획일자' in df_v.columns:
            for idx, row in df_v.iterrows():
                agenda_list.append({
                    'Date': pd.to_datetime(row['계획일자'], errors='coerce'),
                    'Title': f"[검증] {row.get('검증항목', '')}",
                    'Desc': row.get('세부내용', ''),
                    'Status': row.get('상태', '예정'),
                    'Source': VERIFY_FILE,
                    'Idx': idx
                })
                
        if not df_o.empty and '일자' in df_o.columns:
            for idx, row in df_o.iterrows():
                agenda_list.append({
                    'Date': pd.to_datetime(row['일자'], errors='coerce'),
                    'Title': f"[기타] {row.get('일정명', '')}",
                    'Desc': row.get('세부내용', ''),
                    'Status': row.get('상태', '예정'),
                    'Source': OTHER_SCHED_FILE,
                    'Idx': idx
                })
                
        if not df_hc.empty and '검진일자' in df_hc.columns:
            for idx, row in df_hc.iterrows():
                if pd.isna(row['검진일자']): continue
                exam_date = pd.to_datetime(row['검진일자'], errors='coerce')
                if pd.isnull(exam_date): continue
                
                exp_date = exam_date + pd.DateOffset(years=1) - pd.Timedelta(days=1)
                days_left = (exp_date.date() - today_date).days
                
                if days_left <= 30:
                    hc_status = "만료" if days_left < 0 else f"D-{days_left}"
                    alert_prefix = "[보건증 만료]" if days_left < 0 else "[보건증 갱신]"
                    
                    agenda_list.append({
                        'Date': exp_date,
                        'Title': f"🚨 {alert_prefix} {row.get('이름', '')} ({row.get('직급', '')})",
                        'Desc': f"연락처: {row.get('연락처', '')} / 만기일: {exp_date.strftime('%Y-%m-%d')}",
                        'Status': hc_status,
                        'Source': 'HEALTH',
                        'Idx': idx
                    })
                    
        # ✨ 계측기기 차기 검교정일자 캘린더 연동 (D-30 알람)
        if not df_calib_c.empty and '차기_검교정일자' in df_calib_c.columns:
            for idx, row in df_calib_c.iterrows():
                if pd.isna(row['차기_검교정일자']) or str(row['차기_검교정일자']).strip() == "": continue
                try:
                    calib_date = pd.to_datetime(row['차기_검교정일자']).date()
                except: continue
                
                days_left = (calib_date - today_date).days
                
                if days_left <= 30:
                    c_status = "만료" if days_left < 0 else f"D-{days_left}"
                    c_alert = "[검교정 만료]" if days_left < 0 else "[검교정 도래]"
                    
                    agenda_list.append({
                        'Date': pd.to_datetime(calib_date),
                        'Title': f"⚖️ {c_alert} {row.get('검사_설비명', '')} ({row.get('관리번호', '')})",
                        'Desc': f"구분: {row.get('구분', '')} / 주기: {row.get('주기', '')}개월 / 만기일: {calib_date.strftime('%Y-%m-%d')}",
                        'Status': c_status,
                        'Source': 'CALIB',
                        'Idx': idx
                    })

        # ✨ 필터 점검일자 캘린더 연동 (30일 전 자동 알람)
        if not df_filter.empty and '차기점검일자' in df_filter.columns:
            for idx, row in df_filter.iterrows():
                if pd.isna(row['차기점검일자']) or str(row['차기점검일자']).strip() == "": continue
                try:
                    f_date = pd.to_datetime(row['차기점검일자']).date()
                except: continue
                
                days_left = (f_date - today_date).days
                
                if days_left <= 30:
                    f_status = "만료" if days_left < 0 else f"D-{days_left}"
                    f_alert = "[필터 만료]" if days_left < 0 else "[필터 점검]"
                    
                    agenda_list.append({
                        'Date': pd.to_datetime(f_date),
                        'Title': f"🚰 {f_alert} {row.get('설치장소', '')} ({row.get('필터명', '')}) [{row.get('내용', '')}]",
                        'Desc': f"주기: {row.get('주기_개월', '')}개월 / 만기일: {f_date.strftime('%Y-%m-%d')}",
                        'Status': f_status,
                        'Source': 'FILTER',
                        'Idx': idx
                    })
        
        df_agenda = pd.DataFrame(agenda_list, columns=['Date', 'Title', 'Desc', 'Status', 'Source', 'Idx'])
        df_agenda = df_agenda.dropna(subset=['Date']).sort_values('Date')
        
        if df_agenda.empty:
            st.info("임박하거나 등록된 캘린더 일정이 없습니다. 좌측 메뉴에서 항목을 추가해 주세요.")
        else:
            for _, row in df_agenda.iterrows():
                d_val = row['Date'].date()
                status = row['Status']
                source = row['Source']
                
                if status == "완료":
                    disp_status = "완료"; badge_class = "badge-done"
                elif source == 'HEALTH':
                    disp_status = status
                    badge_class = "badge-overdue" if status == "만료" else "badge-warning"
                elif source == 'CALIB' or source == 'FILTER':
                    disp_status = status
                    badge_class = "badge-overdue" if "만료" in status else "badge-warning"
                else:
                    if d_val < today_date: disp_status = "미완료"; badge_class = "badge-overdue"
                    else: disp_status = "예정"; badge_class = "badge-upcoming"
                        
                d_str = row['Date'].strftime("%m/%d")
                
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1.2])
                    with c1:
                        text_style = "text-decoration: line-through; color: #A0A0A0;" if disp_status == "완료" else ""
                        date_color = "#A0A0A0" if disp_status == "완료" else "#D11031"
                        st.markdown(f"<span style='font-size:1.2rem; font-weight:800; color:{date_color}; margin-right:15px;'>{d_str}</span> <span style='font-size:1.1rem; font-weight:700; {text_style}'>{row['Title']}</span> &nbsp;<span class='badge {badge_class}'>{disp_status}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:#6C757D; font-size:0.95rem; margin-left:62px; {text_style}'>{row['Desc']}</span>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                        if source not in ['HEALTH', 'CALIB', 'FILTER']:
                            btn_label = "⏪ 완료 취소" if disp_status == "완료" else "✅ 완료 처리"
                            if st.button(btn_label, key=f"btn_{source}_{row['Idx']}", use_container_width=True):
                                toggle_task_status(source, row['Idx'])
                                st.rerun()
                        elif source == 'HEALTH':
                            st.caption("보건증 메뉴에서 갱신")
                        elif source == 'CALIB':
                            st.caption("계측기기 메뉴에서 갱신")
                        elif source == 'FILTER':
                            st.caption("설비관리 > 필터 점검관리에서 점검일자 갱신 요망")

# --- 2. 캘린더 (하위 메뉴들) ---
elif menu_selection == "캘린더":
    
    if sub_menu == "검증 계획표":
        st.markdown('<div class="section-title">✅ 연간 검증 계획표 관리</div>', unsafe_allow_html=True)
        df_v = load_verify()
        
        with st.expander("➕ 새 검증 계획 등록"):
            with st.form("form_verify"):
                v1, v2 = st.columns(2)
                with v1:
                    v_date = st.date_input("계획 일자")
                    v_type = st.selectbox("검증 종류", ["일상검증", "정기검증", "내부검증", "외부검증", "특별검증"])
                    v_item = st.text_input("검증 항목 (예: 자가품질검사)")
                with v2:
                    v_desc = st.text_input("세부 내용")
                    v_method = st.selectbox("검증 방법", ["기록확인", "현장조사", "시험∙검사", "평가서", "기타"])
                    v_status = st.selectbox("초기 상태", ["예정", "완료"])
                    
                if st.form_submit_button("일정 등록하기"):
                    if v_item:
                        new_df = pd.DataFrame([[str(v_date), v_type, v_item, v_desc, v_method, v_status]], columns=df_v.columns)
                        df_v = pd.concat([df_v, new_df], ignore_index=True)
                        df_v.to_csv(VERIFY_FILE, index=False, encoding='utf-8-sig')
                        st.success("캘린더 연동 완료!")
                        st.rerun()
                    else: st.error("항목을 입력하세요.")
        
        cfg_v = {"상태": st.column_config.SelectboxColumn("상태", options=["예정", "완료"])}
        edited_v = st.data_editor(df_v, num_rows="dynamic", use_container_width=True, column_config=cfg_v)
        if st.button("💾 변경사항 서버에 저장", key="save_v"):
            edited_v.to_csv(VERIFY_FILE, index=False, encoding='utf-8-sig')
            st.rerun()

    elif sub_menu == "기타 일정":
        st.markdown('<div class="section-title">🗓️ 기타 일정 관리</div>', unsafe_allow_html=True)
        df_o = load_other_sched()
        
        with st.expander("➕ 새 일정 등록"):
            with st.form("form_other"):
                o1, o2 = st.columns(2)
                with o1:
                    o_date = st.date_input("일자")
                    o_title = st.text_input("일정명 (예: 식약처 심사)")
                with o2:
                    o_desc = st.text_input("세부 내용")
                    o_status = st.selectbox("상태", ["예정", "완료"])
                
                if st.form_submit_button("일정 등록하기"):
                    if o_title:
                        new_df = pd.DataFrame([[str(o_date), o_title, o_desc, o_status]], columns=df_o.columns)
                        df_o = pd.concat([df_o, new_df], ignore_index=True)
                        df_o.to_csv(OTHER_SCHED_FILE, index=False, encoding='utf-8-sig')
                        st.success("일정 등록 완료!")
                        st.rerun()
                    else: st.error("일정명을 입력하세요.")
                        
        cfg_o = {"상태": st.column_config.SelectboxColumn("상태", options=["예정", "완료"])}
        edited_o = st.data_editor(df_o, num_rows="dynamic", use_container_width=True, column_config=cfg_o)
        if st.button("💾 변경사항 서버에 저장", key="save_o"):
            edited_o.to_csv(OTHER_SCHED_FILE, index=False, encoding='utf-8-sig')
            st.rerun()

# --- 4. 직원 관리 메뉴 ---
elif menu_selection == "직원 관리":
    if sub_menu == "조직도 및 인원 관리":
        st.markdown('<div class="section-title">👥 회사 인원 및 조직도 관리</div>', unsafe_allow_html=True)
        st.write("사내 인원을 등록하면 보건증 현황 등 각종 관리 메뉴에 자동으로 연동되며, 조직도 엑셀 양식을 다운로드할 수 있습니다.")
        
        df_emp = load_employees()
        
        with st.expander("➕ 신규 인원 등록"):
            with st.form("form_employee"):
                e1, e2 = st.columns(2)
                with e1:
                    e_empno = st.text_input("사번 (예: H2026001)")
                    e_name = st.text_input("이름")
                with e2:
                    e_rank = st.text_input("직급 (예: 매니저, 대리, 사원, 팀장)")
                    e_contact = st.text_input("연락처")
                
                c_date, c_stat = st.columns(2)
                with c_date:
                    e_join_date = st.date_input("입사일")
                with c_stat:
                    e_status = st.selectbox("재직 상태", ["재직", "퇴사", "휴직"])

                c_haccp, c_ccp, c_etc = st.columns(3)
                with c_haccp:
                    e_haccp = st.selectbox("HACCP 직책", ["해당없음", "HACCP 팀장", "생산/시설관리팀", "품질관리팀", "업무지원팀"])
                with c_ccp:
                    e_ccp = st.multiselect("모니터링 담당 CCP", ["CCP-1", "CCP-2", "CCP-3", "CCP-4", "CCP-5", "CCP-6"])
                with c_etc:
                    e_etc = st.text_input("기타 (비고)")

                if st.form_submit_button("인원 등록"):
                    if e_name and e_empno:
                        if e_empno in df_emp['사번'].values:
                            st.error("이미 등록된 사번입니다. 다른 사번을 입력해 주세요.")
                        else:
                            ccp_str = ", ".join(e_ccp) if e_ccp else ""
                            new_emp = pd.DataFrame([[e_empno, e_rank, e_name, e_contact, str(e_join_date), e_status, e_haccp, ccp_str, e_etc]], columns=df_emp.columns)
                            df_emp = pd.concat([df_emp, new_emp], ignore_index=True)
                            df_emp.to_csv(EMPLOYEE_FILE, index=False, encoding='utf-8-sig')
                            st.success(f"{e_name} 님 등록이 완료되었습니다!")
                            st.rerun()
                    else:
                        st.error("사번과 이름을 모두 입력하세요.")

        st.markdown("**📋 전체 직원 목록** (아래 표에서 직접 수정할 수 있습니다.)")
        
        cfg_emp = {
            "재직상태": st.column_config.SelectboxColumn("재직상태", options=["재직", "퇴사", "휴직"]),
            "HACCP 직책": st.column_config.SelectboxColumn("HACCP 직책", options=["해당없음", "HACCP 팀장", "생산/시설관리팀", "품질관리팀", "업무지원팀"]),
            "모니터링 CCP": st.column_config.TextColumn("모니터링 CCP (쉼표로 구분하여 수정 가능)"),
            "기타": st.column_config.TextColumn("기타"), 
            "입사일": st.column_config.DateColumn("입사일", format="YYYY-MM-DD")
        }
        
        display_emp = df_emp.copy()
        display_emp['입사일'] = pd.to_datetime(display_emp['입사일'], errors='coerce')
        
        edited_emp = st.data_editor(display_emp, num_rows="dynamic", use_container_width=True, column_config=cfg_emp)
        
        def export_org_excel(df_view):
            df_view = df_view.fillna("") 
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('HACCP조직도')
                
                worksheet.set_paper(9) 
                worksheet.fit_to_pages(1, 1) 
                worksheet.center_horizontally() 
                worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5) 
                
                title_fmt = workbook.add_format({'bold': True, 'font_size': 20, 'align': 'center', 'valign': 'vcenter'})
                doc_info_title_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 1, 'bg_color': '#F2F2F2'})
                doc_info_val_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
                
                header_fmt = workbook.add_format({'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                name_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
                section_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'font_size': 12})
                
                worksheet.set_column('A:A', 3)
                worksheet.set_column('B:G', 16) 
                
                worksheet.merge_range('B2:E4', "HACCP팀 조직도", title_fmt)
                
                worksheet.write('F2', "문서번호", doc_info_title_fmt)
                worksheet.write('G2', "HLSHS-101-A01", doc_info_val_fmt)
                worksheet.write('F3', "제정일자", doc_info_title_fmt)
                worksheet.write('G3', "2018-11-05", doc_info_val_fmt)
                worksheet.write('F4', "개정일자", doc_info_title_fmt)
                worksheet.write('G4', date.today().strftime('%Y-%m-%d'), doc_info_val_fmt)
                
                team_leaders = df_view[df_view['HACCP 직책'] == 'HACCP 팀장']['이름'].tolist()
                leader_name = ", ".join(team_leaders) if team_leaders else "(공란)"
                worksheet.merge_range('D6:E6', "HACCP 팀장", header_fmt)
                worksheet.merge_range('D7:E8', leader_name, name_fmt)
                
                teams = ["생산/시설관리팀", "품질관리팀", "업무지원팀"]
                col_map = {"생산/시설관리팀": 1, "품질관리팀": 3, "업무지원팀": 5} 
                
                max_team_members = 0
                for t in teams:
                    c_idx = col_map[t]
                    worksheet.merge_range(10, c_idx, 10, c_idx+1, t, header_fmt)
                    worksheet.set_row(10, 25)
                    
                    members = df_view[df_view['HACCP 직책'] == t]
                    team_heads = members[members['직급'].str.contains('팀장', na=False)]
                    team_normals = members[~members['직급'].str.contains('팀장', na=False)]
                    sorted_members = pd.concat([team_heads, team_normals])
                    
                    if len(sorted_members) > max_team_members: max_team_members = len(sorted_members)
                    
                    row_idx = 11
                    for _, row in sorted_members.iterrows():
                        info = f"{row['이름']}\n({row['직급']})"
                        worksheet.merge_range(row_idx, c_idx, row_idx, c_idx+1, info, name_fmt)
                        worksheet.set_row(row_idx, 35)
                        row_idx += 1
                    
                    while row_idx <= 11 + 5: 
                        worksheet.merge_range(row_idx, c_idx, row_idx, c_idx+1, "", name_fmt)
                        worksheet.set_row(row_idx, 35)
                        row_idx += 1

                ccp_start_row = 11 + max(max_team_members, 6) + 2
                
                worksheet.merge_range(ccp_start_row, 1, ccp_start_row, 6, "CCP 모니터링 담당", section_fmt)
                worksheet.set_row(ccp_start_row, 25)
                
                ccps = ["CCP-1", "CCP-2", "CCP-3", "CCP-4", "CCP-5", "CCP-6"]
                for i, ccp in enumerate(ccps):
                    c_idx = i + 1  
                    
                    worksheet.write(ccp_start_row + 1, c_idx, ccp, header_fmt)
                    worksheet.set_row(ccp_start_row + 1, 20)
                    
                    assigned = []
                    for _, row in df_view.iterrows():
                        if ccp in str(row['모니터링 CCP']):
                            assigned.append(f"{row['이름']}")
                
                    row_idx = ccp_start_row + 2
                    for name in assigned:
                        worksheet.write(row_idx, c_idx, name, name_fmt)
                        worksheet.set_row(row_idx, 25)
                        row_idx += 1
                    
                    end_row = ccp_start_row + 2 + 5 
                    while row_idx < end_row:
                        worksheet.write(row_idx, c_idx, "", name_fmt)
                        worksheet.set_row(row_idx, 25)
                        row_idx += 1

            return output.getvalue()

        c_e1, c_e2 = st.columns(2)
        with c_e1:
            if st.button("💾 직원 정보 변경사항 저장"):
                edited_emp['입사일'] = edited_emp['입사일'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
                edited_emp.to_csv(EMPLOYEE_FILE, index=False, encoding='utf-8-sig')
                st.success("직원 정보가 성공적으로 업데이트 되었습니다.")
                st.rerun()
                
        with c_e2:
            st.download_button(
                label="📥 HACCP 조직도 엑셀 다운로드 (인쇄 최적화)",
                data=export_org_excel(edited_emp),
                file_name=f"Hollys_OrgChart_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    elif sub_menu == "보건증 현황관리":
        st.markdown('<div class="section-title">🩺 보건증 현황 관리표</div>', unsafe_allow_html=True)
        st.write("직원 보건증 현황을 등록합니다. **검진일로부터 1년 뒤가 만료일로 자동 계산**되며, 30일 전 대시보드 캘린더에 경고 뱃지가 뜹니다.")
        
        df_hc = load_health_cert()
        df_emp = load_employees()
        
        active_emps = df_emp[df_emp["재직상태"] == "재직"] if not df_emp.empty and "재직상태" in df_emp.columns else pd.DataFrame()
        
        with st.expander("➕ 신규 인원 보건증 등록"):
            if active_emps.empty:
                st.warning("등록된 재직 직원이 없습니다. 좌측 메뉴의 '직원 관리'에서 직원을 먼저 등록해 주세요.")
            else:
                with st.form("form_health"):
                    st.caption("아래 목록에서 직원을 선택하면 직급과 연락처가 자동으로 연동되어 저장됩니다.")
                    
                    emp_options = active_emps.apply(lambda x: f"{x['이름']} ({x['직급']}) - {x['사번']}", axis=1).tolist()
                    selected_emp_str = st.selectbox("직원 선택", emp_options)
                    
                    h_date = st.date_input("검진 일자")
                    
                    if st.form_submit_button("보건증 등록"):
                        if selected_emp_str:
                            emp_idx = emp_options.index(selected_emp_str)
                            sel_row = active_emps.iloc[emp_idx]
                            
                            h_rank = sel_row['직급']
                            h_name = sel_row['이름']
                            h_contact = sel_row['연락처']

                            new_df = pd.DataFrame([[h_rank, h_name, h_contact, str(h_date)]], columns=df_hc.columns)
                            df_hc = pd.concat([df_hc, new_df], ignore_index=True)
                            df_hc.to_csv(HEALTH_CERT_FILE, index=False, encoding='utf-8-sig')
                            st.success(f"[{h_name}] 보건증 등록 완료!")
                            st.rerun()

        display_hc = df_hc.copy()
        today = pd.to_datetime(date.today())
        
        exp_dates = []
        d_days = []
        statuses = []
        
        display_hc['검진일자'] = pd.to_datetime(display_hc['검진일자'], errors='coerce')
        
        for _, row in display_hc.iterrows():
            exam = row['검진일자']
            if pd.isna(exam):
                exp_dates.append("")
                d_days.append("")
                statuses.append("미등록")
                continue
            
            exp = exam + pd.DateOffset(years=1) - pd.Timedelta(days=1)
            days_left = (exp - today).days
            
            exp_dates.append(exp.strftime('%Y-%m-%d'))
            d_days.append(days_left)
            if days_left < 0: statuses.append("🔴 만료")
            elif days_left <= 30: statuses.append("🟠 갱신요망")
            else: statuses.append("🟢 정상")
                
        display_hc['만기일자 (자동)'] = exp_dates
        display_hc['D-Day'] = d_days
        display_hc['상태'] = statuses

        st.markdown("**📋 전체 직원 보건증 현황** (아래 표에서 직접 정보/검진일을 더블클릭해 수정할 수 있습니다.)")
        
        cfg_hc = {
            "검진일자": st.column_config.DateColumn("검진일자 (더블클릭)", format="YYYY-MM-DD"),
            "만기일자 (자동)": st.column_config.Column("만기일자 (자동)", disabled=True),
            "D-Day": st.column_config.Column("D-Day", disabled=True),
            "상태": st.column_config.Column("상태", disabled=True)
        }

        edited_hc = st.data_editor(display_hc, num_rows="dynamic", use_container_width=True, column_config=cfg_hc)
        
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            if st.button("💾 보건증 데이터 저장 및 업데이트"):
                save_df = edited_hc[['직급', '이름', '연락처', '검진일자']]
                save_df['검진일자'] = save_df['검진일자'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
                save_df.to_csv(HEALTH_CERT_FILE, index=False, encoding='utf-8-sig')
                st.success("데이터가 저장되었습니다.")
                st.rerun()
                
        def export_health_excel(df_view):
            df_view = df_view.fillna("") 
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('보건증현황')
                
                title_format = workbook.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter'})
                header_format = workbook.add_format({'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                normal_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                alert_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_color': 'red', 'bold': True})
                
                worksheet.merge_range('A1:G1', "건강진단결과(보건증) 현황 관리표", title_format)
                worksheet.set_row(0, 40)
                worksheet.write('A2', f"출력일자: {date.today().strftime('%Y-%m-%d')}")
                
                headers = list(df_view.columns)
                for col_num, header in enumerate(headers):
                    worksheet.write(2, col_num, header, header_format)
                
                for row_num, row in df_view.iterrows():
                    for col_num, col_name in enumerate(headers):
                        val = row[col_name]
                        if isinstance(val, (date, datetime)): val = val.strftime('%Y-%m-%d')
                            
                        is_alert = False
                        if col_name in ['D-Day', '상태']:
                            if val != "" and row['D-Day'] != "":
                                try:
                                    if float(row['D-Day']) <= 30:
                                        is_alert = True
                                except ValueError:
                                    pass
                        
                        if is_alert:
                            worksheet.write(row_num + 3, col_num, val, alert_format)
                        else:
                            worksheet.write(row_num + 3, col_num, val, normal_format)
                
                worksheet.set_column('A:B', 15); worksheet.set_column('C:C', 20)
                worksheet.set_column('D:E', 18); worksheet.set_column('F:G', 15)
                
            return output.getvalue()
            
        with c_h2:
            st.download_button(
                label="📥 보건증 현황 관리표 엑셀 다운로드",
                data=export_health_excel(display_hc),
                file_name=f"Hollys_HealthCert_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# 🌟 5. 설비 관리 메뉴 
elif menu_selection == "설비 관리":
    
    # ✨ 1. 제조위생설비이력관리
    if sub_menu == "제조위생설비이력관리":
        st.markdown('<div class="section-title">🏭 제조위생설비이력관리</div>', unsafe_allow_html=True)
        st.write("공장 내 설비를 등록하고 수리 이력을 관리합니다. 작성된 데이터는 엑셀 양식으로 바로 출력할 수 있습니다.")
        
        if 'selected_facility' not in st.session_state:
            st.session_state.selected_facility = None

        df_fac = load_facilities()
        df_rep = load_repairs()

        if st.session_state.selected_facility is None:
            
            with st.expander("➕ 신규 설비 이력카드 등록"):
                with st.form("form_facility"):
                    col1, col2 = st.columns(2)
                    with col1:
                        f_no = st.text_input("설비번호 (예: F-01)")
                        f_name = st.text_input("설비명")
                        f_usage = st.text_input("사용용도")
                        f_volt = st.text_input("전압")
                        f_year = st.text_input("구입년월")
                    with col2:
                        f_maker = st.text_input("제조회사명")
                        f_loc = st.text_input("설치장소")
                        f_dept = st.text_input("관리부서")
                        f_man_main = st.text_input("관리자 (정)")
                        f_man_sub = st.text_input("관리자 (부)")
                    
                    f_note = st.text_area("특이사항 (모델명, 규격, 안전·방호장치 등)")
                    
                    if st.form_submit_button("설비 등록 완료"):
                        if f_no and f_name:
                            if f_no in df_fac['설비번호'].values:
                                st.error("이미 존재하는 설비번호입니다.")
                            else:
                                new_f = pd.DataFrame([[f_no, f_name, f_usage, f_volt, f_year, f_maker, f_loc, f_dept, f_man_main, f_man_sub, f_note]], columns=df_fac.columns)
                                df_fac = pd.concat([df_fac, new_f], ignore_index=True)
                                df_fac.to_csv(FACILITY_FILE, index=False, encoding='utf-8-sig')
                                st.success(f"[{f_no}] {f_name} 설비 등록 완료!")
                                st.rerun()
                        else: 
                            st.error("설비번호와 설비명은 필수 항목입니다.")

            st.markdown("**📋 전체 등록 설비 목록 (DB)**")
            edited_fac = st.data_editor(df_fac, num_rows="dynamic", use_container_width=True)
            
            def export_facility_list(df_list):
                df_list = df_list.fillna("")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
                    wb = writer.book
                    ws = wb.add_worksheet('설비목록표')
                    
                    ws.set_paper(9)
                    ws.fit_to_pages(1, 0)
                    
                    title_fmt = wb.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter'})
                    header_fmt = wb.add_format({'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                    val_fmt = wb.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                    
                    ws.merge_range('A1:K2', "제조위생설비 목록표", title_fmt)
                    
                    headers = list(df_list.columns)
                    for col_num, header in enumerate(headers):
                        ws.write(3, col_num, header, header_fmt)
                        ws.set_column(col_num, col_num, 12 if col_num != 10 else 35) 
                        
                    for r_idx, row in df_list.iterrows():
                        for c_idx, col_name in enumerate(headers):
                            ws.write(r_idx + 4, c_idx, str(row[col_name]), val_fmt)
                            ws.set_row(r_idx + 4, 25)
                            
                return output.getvalue()

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                if st.button("💾 설비 목록 정보 일괄 저장"):
                    edited_fac.to_csv(FACILITY_FILE, index=False, encoding='utf-8-sig')
                    st.success("설비 DB가 성공적으로 업데이트 되었습니다.")
                    st.rerun()
            with c_f2:
                st.download_button(
                    "📥 설비 목록표 엑셀 다운로드", 
                    data=export_facility_list(edited_fac), 
                    file_name=f"Hollys_FacilityList_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            st.markdown("---")
            st.markdown("**🔍 개별 설비 이력 카드 관리 (사진 첨부 및 수리내역 작성)**")
            st.write("아래 설비 카드의 버튼을 클릭하면 세부 이력 카드로 진입합니다.")
            
            if df_fac.empty:
                st.info("등록된 설비가 없습니다.")
            else:
                cols = st.columns(4)
                for idx, row in df_fac.iterrows():
                    f_no_val = row['설비번호']
                    f_name_val = row['설비명']
                    f_loc_val = row['설치장소']
                    with cols[idx % 4]:
                        with st.container(border=True):
                            st.markdown(f"<h4 style='color: #D11031; margin-bottom: 0;'>{f_no_val}</h4>", unsafe_allow_html=True)
                            st.markdown(f"**{f_name_val}**")
                            st.caption(f"장소: {f_loc_val}")
                            if st.button("이력카드 열람 📝", key=f"btn_fac_{f_no_val}", use_container_width=True):
                                st.session_state.selected_facility = f_no_val
                                st.rerun()

        else: 
            # --- 개별 설비 상세(이력카드) 페이지 ---
            sel_fno = st.session_state.selected_facility
            filtered_fac = df_fac[df_fac['설비번호'] == sel_fno]
            
            if filtered_fac.empty:
                st.warning(f"선택한 설비({sel_fno}) 정보를 찾을 수 없습니다. 데이터가 삭제되었거나 번호가 변경되었습니다.")
                if st.button("⬅️ 설비 목록으로 돌아가기"):
                    st.session_state.selected_facility = None
                    st.rerun()
            else:
                f_row = filtered_fac.iloc[0]
                
                col_fb1, col_fb2 = st.columns([1, 6])
                with col_fb1:
                    if st.button("⬅️ 설비 목록으로", use_container_width=True):
                        st.session_state.selected_facility = None
                        st.rerun()
                with col_fb2:
                    st.markdown(f"<h3 style='margin-top: 0;'>[{sel_fno}] {f_row['설비명']} 제조위생설비 이력카드</h3>", unsafe_allow_html=True)
                    
                c_info, c_img = st.columns([1.5, 1])
                IMG_FILE = f"fac_photo_{sel_fno}.png"
                
                with c_info:
                    st.markdown('<div class="section-title">■ 1. 기계 기본 정보</div>', unsafe_allow_html=True)
                    info_df = pd.DataFrame({
                        "분류": ["설비명", "사용용도", "구입년월", "설치장소", "관리자(정)", "특이사항"],
                        "항목 내용": [f_row['설비명'], f_row['사용용도'], f_row['구입년월'], f_row['설치장소'], f_row['관리자_정'], f_row['특이사항']],
                        "분류_2": ["설비번호", "전압", "제조회사명", "관리부서", "관리자(부)", ""],
                        "항목 내용_2": [f_row['설비번호'], f_row['전압'], f_row['제조회사명'], f_row['관리부서'], f_row['관리자_부'], ""]
                    })
                    st.table(info_df)
                    
                with c_img:
                    st.markdown('<div class="section-title">■ 2. 기계 사진</div>', unsafe_allow_html=True)
                    upl_img = st.file_uploader("📥 기계 사진 등록 (PNG, JPG)", type=['png', 'jpg', 'jpeg'])
                    if upl_img:
                        with open(IMG_FILE, "wb") as f: f.write(upl_img.getbuffer())
                        st.rerun()
                    if os.path.exists(IMG_FILE):
                        st.image(IMG_FILE, use_container_width=True)
                        if st.button("🗑️ 사진 삭제", use_container_width=True):
                            os.remove(IMG_FILE)
                            st.rerun()
                            
                st.markdown('<div class="section-title">■ 3. 수리 이력 사항</div>', unsafe_allow_html=True)
                
                my_repairs = df_rep[df_rep['설비번호'] == sel_fno].copy()
                
                with st.form("form_repair"):
                    c_r1, c_r2, c_r3, c_r4 = st.columns([1, 2, 1, 1])
                    with c_r1: r_date = st.date_input("수리일자")
                    with c_r2: r_detail = st.text_input("수리사항 (내용)")
                    with c_r3: r_shop = st.text_input("수리처")
                    with c_r4: r_note = st.text_input("비고")
                    if st.form_submit_button("수리 내역 추가"):
                        if r_detail:
                            new_r = pd.DataFrame([[sel_fno, str(r_date), r_detail, r_shop, r_note]], columns=df_rep.columns)
                            df_rep = pd.concat([df_rep, new_r], ignore_index=True)
                            df_rep.to_csv(REPAIR_FILE, index=False, encoding='utf-8-sig')
                            st.success("수리 내역 추가 완료!")
                            st.rerun()
                        else:
                            st.error("수리사항 내용을 입력해 주세요.")
                            
                st.markdown("**수리 내역 열람 및 수정** (표에서 바로 수정 후 하단 저장 버튼 클릭)")
                
                cfg_rep = {
                    "수리일자": st.column_config.DateColumn("수리일자", format="YYYY-MM-DD")
                }
                
                display_rep = my_repairs.drop(columns=['설비번호']).copy()
                display_rep['수리일자'] = pd.to_datetime(display_rep['수리일자'], errors='coerce')
                
                edited_rep = st.data_editor(display_rep, num_rows="dynamic", use_container_width=True, column_config=cfg_rep)
                
                def export_facility_excel(f_data, r_data, img_path):
                    f_data = f_data.fillna("") 
                    r_data = r_data.fillna("")
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
                        wb = writer.book
                        ws = wb.add_worksheet('설비이력카드')
                        
                        title_fmt = wb.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter'})
                        doc_fmt = wb.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True})
                        header_fmt = wb.add_format({'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                        val_fmt = wb.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
                        val_left_fmt = wb.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
                        section_fmt = wb.add_format({'bold': True, 'font_size': 12, 'valign': 'vcenter'})
                        
                        ws.set_paper(9)
                        ws.fit_to_pages(1, 1)
                        ws.center_horizontally()
                        ws.set_margins(0.5, 0.5, 0.5, 0.5)
                        
                        ws.set_column('A:A', 12)
                        ws.set_column('B:B', 15)
                        ws.set_column('C:C', 12)
                        ws.set_column('D:D', 15)
                        ws.set_column('E:E', 12)
                        ws.set_column('F:F', 20)
                        
                        ws.merge_range('A1:F2', "제조위생설비 이력카드", title_fmt)
                        ws.write('F3', "문서번호", doc_fmt)
                        ws.write('F4', "HLSPP-203-F02", wb.add_format({'align': 'right', 'valign': 'vcenter'}))
                        
                        ws.merge_range('A6:D6', "1. 기계기본정보", section_fmt)
                        ws.merge_range('E6:F6', "2. 기계사진", section_fmt)
                        
                        ws.write('A7', '설비명', header_fmt)
                        ws.write('B7', f_data['설비명'], val_fmt)
                        ws.write('C7', '설비번호', header_fmt)
                        ws.write('D7', f_data['설비번호'], val_fmt)
                        
                        ws.write('A8', '사용용도', header_fmt)
                        ws.write('B8', f_data['사용용도'], val_fmt)
                        ws.write('C8', '전압', header_fmt)
                        ws.write('D8', f_data['전압'], val_fmt)
                        
                        ws.write('A9', '구입년월', header_fmt)
                        ws.write('B9', f_data['구입년월'], val_fmt)
                        ws.write('C9', '제조회사명', header_fmt)
                        ws.write('D9', f_data['제조회사명'], val_fmt)
                        
                        ws.write('A10', '설치장소', header_fmt)
                        ws.write('B10', f_data['설치장소'], val_fmt)
                        ws.write('C10', '관리부서', header_fmt)
                        ws.write('D10', f_data['관리부서'], val_fmt)
                        
                        ws.merge_range('A11:A12', '관리자', header_fmt)
                        ws.write('B11', '정', header_fmt)
                        ws.merge_range('C11:D11', f_data['관리자_정'], val_fmt)
                        
                        ws.write('B12', '부', header_fmt)
                        ws.merge_range('C12:D12', f_data['관리자_부'], val_fmt)
                        
                        ws.merge_range('A13:A16', '특이사항', header_fmt)
                        ws.merge_range('B13:D16', f_data['특이사항'], val_left_fmt)
                        
                        ws.merge_range('E7:F16', '', val_fmt)
                        if os.path.exists(img_path):
                            try: ws.insert_image('E7', img_path, {'x_offset': 5, 'y_offset': 5, 'object_position': 1, 'x_scale': 0.25, 'y_scale': 0.25})
                            except: pass
                        
                        for r in range(6, 16): ws.set_row(r, 22)
                        
                        ws.merge_range('A18:F18', "3. 수리이력사항", section_fmt)
                        ws.write('A19', '수리일자', header_fmt)
                        ws.merge_range('B19:C19', '수리사항', header_fmt)
                        ws.merge_range('D19:E19', '수리처', header_fmt)
                        ws.write('F19', '비고', header_fmt)
                        
                        r_idx = 19
                        for _, row in r_data.iterrows():
                            val_date = row.get('수리일자', '')
                            if isinstance(val_date, (date, datetime)): val_date = val_date.strftime('%Y-%m-%d')
                            ws.write(r_idx, 0, str(val_date), val_fmt)
                            ws.merge_range(r_idx, 1, r_idx, 2, str(row.get('수리사항', '')), val_fmt)
                            ws.merge_range(r_idx, 3, r_idx, 4, str(row.get('수리처', '')), val_fmt)
                            ws.write(r_idx, 5, str(row.get('비고', '')), val_fmt)
                            ws.set_row(r_idx, 22)
                            r_idx += 1
                            
                        while r_idx < 35:
                            ws.write(r_idx, 0, "", val_fmt)
                            ws.merge_range(r_idx, 1, r_idx, 2, "", val_fmt)
                            ws.merge_range(r_idx, 3, r_idx, 4, "", val_fmt)
                            ws.write(r_idx, 5, "", val_fmt)
                            ws.set_row(r_idx, 22)
                            r_idx += 1
                            
                    return output.getvalue()
                    
                c_br1, c_br2 = st.columns(2)
                with c_br1:
                    if st.button("💾 수리 이력 변경사항 저장", use_container_width=True):
                        df_rep = df_rep[df_rep['설비번호'] != sel_fno]
                        edited_rep['설비번호'] = sel_fno
                        edited_rep['수리일자'] = edited_rep['수리일자'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
                        df_rep = pd.concat([df_rep, edited_rep], ignore_index=True)
                        df_rep.to_csv(REPAIR_FILE, index=False, encoding='utf-8-sig')
                        st.success("저장 완료!")
                        st.rerun()
                        
                with c_br2:
                    st.download_button(
                        label="🖨️ 해당 설비이력카드 엑셀 다운로드 (인쇄 최적화)",
                        data=export_facility_excel(f_row, edited_rep, IMG_FILE),
                        file_name=f"Hollys_FacilityCard_{sel_fno}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

    # ✨ 2. 필터 점검관리
    elif sub_menu == "필터 점검관리":
        st.markdown('<div class="section-title">🚰 필터 점검 관리 (계획표)</div>', unsafe_allow_html=True)
        st.write("각종 필터(정수기, 공조기, 집진기 등)의 점검(교체/세척) 주기를 캘린더와 연동하여 관리하고 계획표를 출력합니다.")

        df_filter = load_filter_plan()

        with st.expander("➕ 새 필터 점검 항목 등록"):
            with st.form("form_filter"):
                f1, f2, f3 = st.columns(3)
                with f1:
                    flt_loc = st.text_input("설치장소 (예: 로스팅룸, 1층)")
                    flt_type = st.text_input("필터명 (예: 카본필터, 헤파필터)")
                with f2:
                    flt_content = st.selectbox("내용", ["교체", "세척"])
                    flt_cycle = st.number_input("주기 (개월)", min_value=1, step=1, value=6)
                with f3:
                    flt_date = st.date_input("점검일자")
                    flt_note = st.text_input("비고 (특이사항)")

                if st.form_submit_button("필터 등록하기"):
                    if flt_loc and flt_type:
                        next_date = flt_date + pd.DateOffset(months=flt_cycle)
                        new_df = pd.DataFrame([[flt_loc, flt_type, flt_content, flt_cycle, str(flt_date), str(next_date.date()), "예정", flt_note]], columns=df_filter.columns)
                        df_filter = pd.concat([df_filter, new_df], ignore_index=True)
                        df_filter.to_csv(FILTER_PLAN_FILE, index=False, encoding='utf-8-sig')
                        st.success("필터 등록 완료! 대시보드 캘린더에 연동되었습니다.")
                        st.rerun()
                    else:
                        st.error("설치장소와 필터명을 입력하세요.")

        view_df_filter = df_filter.copy()
        view_df_filter['점검일자'] = pd.to_datetime(view_df_filter['점검일자'], errors='coerce')
        view_df_filter['주기_개월'] = pd.to_numeric(view_df_filter['주기_개월'], errors='coerce')

        def calc_next_filter(row):
            if pd.notna(row['점검일자']) and pd.notna(row['주기_개월']):
                try: return row['점검일자'] + pd.DateOffset(months=int(row['주기_개월']))
                except: return pd.NaT
            return pd.NaT

        view_df_filter['차기점검일자'] = view_df_filter.apply(calc_next_filter, axis=1)

        cfg_filter = {
            "내용": st.column_config.SelectboxColumn("내용", options=["교체", "세척"]),
            "점검일자": st.column_config.DateColumn("점검일자", format="YYYY-MM-DD"),
            "차기점검일자": st.column_config.DateColumn("차기점검일자 (자동)", format="YYYY-MM-DD", disabled=True),
            "주기_개월": st.column_config.NumberColumn("주기 (개월)", min_value=1, step=1, format="%d"),
            "상태": st.column_config.SelectboxColumn("상태", options=["예정", "완료"])
        }

        st.markdown("**📋 등록된 필터 점검 목록** (아래 표에서 텍스트와 날짜를 직접 수정 가능합니다)")
        st.caption("💡 점검 완료 시 이곳에서 **점검일자**를 갱신해주시면 대시보드 캘린더의 차기 점검 알람이 자동으로 연장됩니다.")
        edited_filter = st.data_editor(view_df_filter, num_rows="dynamic", use_container_width=True, column_config=cfg_filter)

        def export_filter_excel(df_view):
            df_view = df_view.fillna("")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
                wb = writer.book
                ws = wb.add_worksheet('필터점검계획표')
                
                ws.set_paper(9) # A4
                ws.fit_to_pages(1, 0)
                
                title_fmt = wb.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter'})
                header_fmt = wb.add_format({'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                val_fmt = wb.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                
                ws.merge_range('A1:H2', f"{date.today().year}년 필터 점검 계획 및 기록표", title_fmt)
                
                headers = ["설치장소", "필터명", "내용(교체/세척)", "주기(개월)", "점검일자", "차기점검일자", "상태", "비고"]
                for c, h in enumerate(headers):
                    ws.write(3, c, h, header_fmt)
                
                ws.set_column('A:A', 18)
                ws.set_column('B:B', 20)
                ws.set_column('C:C', 15)
                ws.set_column('D:D', 12)
                ws.set_column('E:F', 15)
                ws.set_column('G:G', 10)
                ws.set_column('H:H', 20)
                
                r_idx = 4
                for _, row in df_view.iterrows():
                    ws.write(r_idx, 0, str(row.get('설치장소', '')), val_fmt)
                    ws.write(r_idx, 1, str(row.get('필터명', '')), val_fmt)
                    ws.write(r_idx, 2, str(row.get('내용', '')), val_fmt)
                    ws.write(r_idx, 3, str(row.get('주기_개월', '')), val_fmt)
                    
                    d1 = row.get('점검일자', '')
                    if isinstance(d1, (datetime, pd.Timestamp, date)): d1 = d1.strftime('%Y-%m-%d')
                    ws.write(r_idx, 4, str(d1), val_fmt)
                    
                    d2 = row.get('차기점검일자', '')
                    if isinstance(d2, (datetime, pd.Timestamp, date)): d2 = d2.strftime('%Y-%m-%d')
                    ws.write(r_idx, 5, str(d2), val_fmt)
                    
                    ws.write(r_idx, 6, str(row.get('상태', '')), val_fmt)
                    ws.write(r_idx, 7, str(row.get('비고', '')), val_fmt)
                    ws.set_row(r_idx, 25)
                    r_idx += 1
                    
            return output.getvalue()

        c_filt1, c_filt2 = st.columns(2)
        with c_filt1:
            if st.button("💾 필터 점검표 저장 및 업데이트"):
                edited_filter['점검일자'] = pd.to_datetime(edited_filter['점검일자'], errors='coerce')
                edited_filter['주기_개월'] = pd.to_numeric(edited_filter['주기_개월'], errors='coerce')
                edited_filter['차기점검일자'] = edited_filter.apply(calc_next_filter, axis=1)

                edited_filter['점검일자'] = edited_filter['점검일자'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
                edited_filter['차기점검일자'] = edited_filter['차기점검일자'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
                edited_filter['주기_개월'] = edited_filter['주기_개월'].apply(lambda x: str(int(x)) if pd.notna(x) else "")

                edited_filter.to_csv(FILTER_PLAN_FILE, index=False, encoding='utf-8-sig')
                st.success("성공적으로 저장 및 차기 점검일이 갱신되었습니다.")
                st.rerun()
                
        with c_filt2:
            st.download_button(
                label="📥 필터점검계획표 엑셀 다운로드 (보관용)",
                data=export_filter_excel(edited_filter),
                file_name=f"Hollys_FilterPlan_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # ✨ 3. 11분류 체계로 개편된 세척소독 기준
    elif sub_menu == "세척소독 기준":
        st.markdown('<div class="section-title">🧽 SSOP 위생·세척소독 기준표 관리</div>', unsafe_allow_html=True)
        st.write("위생표준작업절차(SSOP)에 따른 11가지 카테고리별 세척·소독 기준을 엑셀과 같은 형식으로 상세히 관리합니다. **식품 제조시설**은 설비 이력카드와 연동됩니다.")

        df_clean = load_cleaning_specs()
        df_fac = load_facilities()

        with st.expander("➕ 새 기준 및 세척방법 추가", expanded=False):
            selected_cat = st.selectbox("📌 대분류 선택", CLEAN_CATEGORIES)
            
            with st.form("form_clean_add"):
                c1, c2 = st.columns(2)
                with c1:
                    # 카테고리가 5. 식품 제조시설일 경우 설비 데이터 연동
                    if selected_cat == "5. 식품 제조시설":
                        if df_fac.empty:
                            st.warning("등록된 설비가 없습니다. 제조위생설비이력관리에서 먼저 등록해주세요.")
                            c_target = st.text_input("관리 대상/설비명 (임시 입력)")
                        else:
                            fac_options = df_fac.apply(lambda x: f"[{x['설비번호']}] {x['설비명']}", axis=1).tolist()
                            c_target = st.selectbox("연동할 대상 설비 선택", fac_options)
                    else:
                        c_target = st.text_input("관리 대상 (예: 바닥, 위생화, 손, 환풍기 등)")
                        
                    c_part = st.text_input("세부 관리 부위/항목 (예: 손가락 사이, 모터팬, 내부 등)")
                
                with c2:
                    c_cycle = st.text_input("청소/소독 주기 (예: 1회/일, 작업 전후)")
                    c_tool = st.text_input("사용 세제/도구 (예: 70% 알코올, 폼크린)")
                    c_manager = st.text_input("책임자 (예: 생산팀 담당자)")

                c_method = st.text_area("세척·소독 방법 (세부 작업 절차를 상세히 기재)")
                
                # 🔥 5분류(식품 제조시설)가 아닌 경우에만 폼 내부에서 사진 업로더 노출
                uploaded_photo = None
                if selected_cat != "5. 식품 제조시설":
                    uploaded_photo = st.file_uploader("📸 현장 사진 등록 (선택사항)", type=['jpg', 'jpeg', 'png'])

                if st.form_submit_button("위생 기준 등록"):
                    if c_target and c_part:
                        new_id = f"C-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        saved_img_path = ""
                        # 사진이 첨부되었으면 저장 처리
                        if uploaded_photo is not None:
                            saved_img_path = f"clean_photo_{new_id}.png"
                            with open(saved_img_path, "wb") as f:
                                f.write(uploaded_photo.getbuffer())

                        new_row = pd.DataFrame([[new_id, selected_cat, '일반구역', c_target, c_part, c_method, c_cycle, c_tool, c_manager, saved_img_path]], columns=df_clean.columns)
                        df_clean = pd.concat([df_clean, new_row], ignore_index=True)
                        df_clean.to_csv(CLEAN_FILE, index=False, encoding='utf-8-sig')
                        
                        st.success("위생 기준이 성공적으로 등록되었습니다!")
                        st.rerun()
                    else:
                        st.error("관리 대상과 부위 항목은 필수입니다.")

        st.markdown("### 📋 전체 세척소독 기준 텍스트 일괄 편집")
        st.caption("표에서 셀을 더블클릭하여 내용을 한 번에 수정할 수 있습니다.")
        cfg_clean = {
            "ID": st.column_config.Column(disabled=True, width="small"),
            "대분류": st.column_config.SelectboxColumn("대분류", options=CLEAN_CATEGORIES),
            "구역": st.column_config.TextColumn("구역", width="small"),
            "사진파일": st.column_config.Column("사진 경로", disabled=True)
        }
        edited_clean = st.data_editor(df_clean, num_rows="dynamic", use_container_width=True, column_config=cfg_clean)
        
        def export_cleaning_excel(df_view):
            df_view = df_view.fillna("")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
                wb = writer.book
                ws = wb.add_worksheet('세척소독 기준표')

                title_fmt = wb.add_format({'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter'})
                header_fmt = wb.add_format({'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True})
                val_fmt = wb.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
                left_fmt = wb.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})

                ws.merge_range('A1:H2', "SSOP 11분류 세척소독 기준표", title_fmt)

                headers = ['대분류', '관리대상/설비명', '부위', '세척·소독 방법', '주기', '사용세제/도구', '책임자', '현장 사진']
                for c, h in enumerate(headers):
                    ws.write(3, c, h, header_fmt)

                ws.set_column('A:A', 15); ws.set_column('B:C', 15)
                ws.set_column('D:D', 35)
                ws.set_column('E:G', 15); ws.set_column('H:H', 22)

                r_idx = 4
                for _, row in df_view.sort_values(by="대분류").iterrows():
                    ws.write(r_idx, 0, str(row.get('대분류', '')), val_fmt)
                    ws.write(r_idx, 1, str(row.get('설비명', '')), val_fmt)
                    ws.write(r_idx, 2, str(row.get('부위', '')), val_fmt)
                    ws.write(r_idx, 3, str(row.get('세척소독방법', '')), left_fmt)
                    ws.write(r_idx, 4, str(row.get('주기', '')), val_fmt)
                    ws.write(r_idx, 5, str(row.get('사용도구', '')), val_fmt)
                    ws.write(r_idx, 6, str(row.get('책임자', '')), val_fmt)

                    img_path = str(row.get('사진파일', ''))
                    ws.write(r_idx, 7, "", val_fmt)
                    
                    # 엑셀 사진 삽입 로직 (5분류 자동 연동 처리)
                    real_img_path = img_path
                    if row.get('대분류') == "5. 식품 제조시설":
                        match = re.search(r'\[(.*?)\]', str(row.get('설비명', '')))
                        if match:
                            f_no = match.group(1)
                            real_img_path = f"fac_photo_{f_no}.png"
                            
                    if real_img_path and os.path.exists(real_img_path):
                        try: ws.insert_image(r_idx, 7, real_img_path, {'x_offset': 5, 'y_offset': 5, 'x_scale': 0.12, 'y_scale': 0.12, 'positioning': 1})
                        except: pass
                        
                    ws.set_row(r_idx, 75)
                    r_idx += 1
            return output.getvalue()

        col_ex_btn1, col_ex_btn2 = st.columns([1, 3])
        with col_ex_btn1:
            if st.button("💾 세척기준 텍스트 변경사항 저장", use_container_width=True):
                edited_clean.to_csv(CLEAN_FILE, index=False, encoding='utf-8-sig')
                st.success("데이터베이스에 정상적으로 반영되었습니다.")
                st.rerun()
        with col_ex_btn2:
            st.download_button(
                label="📥 SSOP 세척소독기준표 엑셀 다운로드 (보고서 제출용)",
                data=export_cleaning_excel(df_clean),
                file_name=f"Hollys_SSOP_Specs_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.divider()
        st.markdown("### 📸 카테고리별 상세 정보 및 현장 사진 관리")
        
        # 탭을 활용한 11개 대분류 화면 구성
        tab_names = [c.split('. ')[1] for c in CLEAN_CATEGORIES]
        tabs = st.tabs(tab_names)

        for i, tab in enumerate(tabs):
            cat_name = CLEAN_CATEGORIES[i]
            with tab:
                df_cat = df_clean[df_clean['대분류'] == cat_name]
                if df_cat.empty:
                    st.info(f"등록된 '{cat_name}' 기준이 없습니다.")
                else:
                    for idx, row in df_cat.iterrows():
                        with st.container(border=True):
                            c_img, c_desc = st.columns([1, 3])
                            part_id = row['ID']
                            target_name = row['설비명']
                            part_name = row['부위']
                            img_path = row['사진파일']

                            with c_img:
                                # 5. 식품 제조시설일 경우 설비 이력카드 사진을 연동하여 표기합니다.
                                if cat_name == "5. 식품 제조시설":
                                    match = re.search(r'\[(.*?)\]', target_name)
                                    if match:
                                        f_no = match.group(1)
                                        fac_img_path = f"fac_photo_{f_no}.png"
                                        if os.path.exists(fac_img_path):
                                            st.image(fac_img_path, use_container_width=True)
                                            st.caption("※ 제조위생설비이력관리 사진 자동연동됨")
                                        else:
                                            st.info("이력카드 사진 미등록")
                                    else:
                                        st.warning("설비 연동 실패 (직접 입력값)")
                                        
                                # 기타 분류인 경우 개별 사진 직접 업로드 방식을 사용합니다.
                                else:
                                    if img_path and os.path.exists(str(img_path)):
                                        st.image(str(img_path), use_container_width=True)
                                        if st.button("🗑️ 등록된 사진 삭제", key=f"del_img_{part_id}"):
                                            os.remove(img_path)
                                            df_clean.loc[df_clean['ID'] == part_id, '사진파일'] = ""
                                            df_clean.to_csv(CLEAN_FILE, index=False, encoding='utf-8-sig')
                                            st.rerun()
                                    else:
                                        up_f = st.file_uploader(f"사진 추가 등록 ({part_name})", key=f"up_{part_id}", type=['jpg','png'])
                                        if up_f:
                                            new_img_path = f"clean_photo_{part_id}.png"
                                            with open(new_img_path, "wb") as f:
                                                f.write(up_f.getbuffer())
                                            df_clean.loc[df_clean['ID'] == part_id, '사진파일'] = new_img_path
                                            df_clean.to_csv(CLEAN_FILE, index=False, encoding='utf-8-sig')
                                            st.rerun()

                            with c_desc:
                                st.markdown(f"<h5 style='color: #D11031;'>▶ 관리대상: {target_name} &nbsp;|&nbsp; 부위: {part_name}</h5>", unsafe_allow_html=True)
                                st.markdown(f"**🔹 세척·소독 방법:** \n{row['세척소독방법']}")
                                st.markdown(f"**🔹 주기:** {row['주기']} &nbsp;|&nbsp; **🔹 세제/도구:** {row['사용도구']} &nbsp;|&nbsp; **🔹 담당/책임:** {row['책임자']}")


# --- 6. 제품 관리 메뉴 ---
elif menu_selection == "제품 관리":
    if sub_menu == "간편 판정 규격":
        st.markdown('<div class="section-title">📦 제품별 간편 판정 규격 관리</div>', unsafe_allow_html=True)
        st.write("생산 기록 등록 시 합불 판정의 기준이 되는 제품 규격을 관리합니다.")
        
        df_specs = load_specs()
        edited_specs = st.data_editor(df_specs, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 제품 규격 저장"):
            edited_specs.to_csv(SPEC_FILE, index=False, encoding='utf-8-sig')
            st.success("제품 규격이 안전하게 저장되었습니다.")
            st.rerun()
            
    elif sub_menu == "상세 규격서 마스터":
        st.markdown('<div class="section-title">📄 상세 규격서 마스터 정보</div>', unsafe_allow_html=True)
        st.info("상세 규격서 및 원부재료 배합비 파일 관리 기능은 업데이트 준비 중입니다.")

# --- 7. 현장 측정 기록 ---
elif menu_selection == "현장 측정 기록":
    st.subheader("📝 현장 측정 기록")
    if df_specs.empty: st.warning("제품 관리 메뉴에서 규격을 먼저 등록해 주세요.")
    else:
        with st.form("record_form"):
            c1, c2 = st.columns(2)
            with c1: prod_date = st.date_input("생산일", datetime.now())
            with c2: target_product = st.selectbox("측정 제품 선택", df_specs["제품명"].tolist())
            spec_row = df_specs[df_specs["제품명"] == target_product].iloc[0]
            p_type, n2, moisture, color, date_record = spec_row["유형"], "N/A", "N/A", "N/A", "N/A"
            ext_times = []
            
            c_val1, c_val2, c_val3 = st.columns(3)
            with c_val1:
                if not pd.isna(spec_row['최소_질소']) and spec_row['최소_질소'] != "N/A": 
                    n2 = st.number_input(f"질소 (%) [기준: {spec_row['최소_질소']}~{spec_row['최대_질소']}]", value=0.0)
            with c_val2:
                if not pd.isna(spec_row['최소_수분']) and spec_row['최소_수분'] != "N/A": 
                    moisture = st.number_input(f"수분 (%) [기준: {spec_row['최소_수분']}~{spec_row['최대_수분']}]", value=0.0)
            with c_val3:
                if not pd.isna(spec_row['최소_색도']) and spec_row['최소_색도'] != "N/A": 
                    color = st.number_input(f"색도 [기준: {spec_row['최소_색도']}~{spec_row['최대_색도']}]", value=0.0)

            if not pd.isna(spec_row['최소_추출']) and spec_row['최소_추출'] != "N/A":
                st.write(f"**⏱️ 추출시간 10회 (합격: 평균 {spec_row['최소_추출']}초~{spec_row['최대_추출']}초)**")
                cols = st.columns(5) * 2
                for i in range(10): ext_times.append(cols[i].number_input(f"{i+1}회(초)", value=0.0, step=0.1, key=f"e_{i}"))

            if st.form_submit_button("저장 및 판정"):
                is_pass, fail_reason = True, []
                ext_avg = sum(ext_times) / 10 if ext_times else "N/A"
                if n2 != "N/A" and not (float(spec_row['최소_질소']) <= float(n2) <= float(spec_row['최대_질소'])): is_pass, fail_reason = False, fail_reason + ["질소"]
                if moisture != "N/A" and not (float(spec_row['최소_수분']) <= float(moisture) <= float(spec_row['최대_수분'])): is_pass, fail_reason = False, fail_reason + ["수분"]
                
                final_status = "PASS" if is_pass else "FAIL"
                new_row = pd.DataFrame([[prod_date, p_type, target_product, n2, moisture, color, ext_avg, date_record, final_status, ""]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                st.success("저장 완료!") if is_pass else st.error(f"부적격! 이탈항목: {fail_reason}")
                st.rerun()

# --- 8. 데이터 히스토리 ---
elif menu_selection == "데이터 히스토리":
    st.subheader("📂 데이터 히스토리")
    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("히스토리 저장"): 
            edited_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.rerun()

# --- 9. 계측기기 검교정 ---
elif menu_selection == "계측기기 검교정":
    st.markdown('<div class="section-title">⚖️ 계측기기 검교정 대장 및 성적서 관리</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 계측기기 검교정 대장 (Master)", "📑 사내 검교정 성적서 발행"])
    
    with tab1:
        st.write("사내에서 관리 중인 모든 계측기기의 목록 및 차기 검교정 일자를 관리합니다.")
        df_calib = load_calib_list()
        
        c_filter1, c_filter2 = st.columns([1, 3])
        with c_filter1:
            calib_type_filter = st.selectbox("검교정 구분 필터", ["전체", "사내(자체)", "사외(의뢰)"])
        
        view_df_calib = df_calib.copy()
        if calib_type_filter != "전체":
            view_df_calib = view_df_calib[view_df_calib["구분"] == calib_type_filter]

        view_df_calib['주기'] = pd.to_numeric(view_df_calib['주기'], errors='coerce')
        view_df_calib['검교정일자'] = pd.to_datetime(view_df_calib['검교정일자'], errors='coerce')

        def calc_next_calib(row):
            if pd.notna(row['검교정일자']) and pd.notna(row['주기']):
                try: return row['검교정일자'] + pd.DateOffset(months=int(row['주기']))
                except: return pd.NaT
            return pd.NaT

        view_df_calib['차기_검교정일자'] = view_df_calib.apply(calc_next_calib, axis=1)
            
        cfg_calib = {
            "구분": st.column_config.SelectboxColumn("구분", options=["사내(자체)", "사외(의뢰)"]),
            "주기": st.column_config.NumberColumn("주기(개월)", min_value=1, step=1, format="%d"),
            "검교정일자": st.column_config.DateColumn("검교정일자", format="YYYY-MM-DD"),
            "차기_검교정일자": st.column_config.DateColumn("차기 검교정일자 (자동)", format="YYYY-MM-DD", disabled=True)
        }
        
        edited_calib = st.data_editor(view_df_calib, num_rows="dynamic", use_container_width=True, column_config=cfg_calib)
        
        if st.button("💾 검교정 대장 서버에 저장", key="save_calib_master"):
            edited_calib['주기'] = pd.to_numeric(edited_calib['주기'], errors='coerce')
            edited_calib['검교정일자'] = pd.to_datetime(edited_calib['검교정일자'], errors='coerce')
            edited_calib['차기_검교정일자'] = edited_calib.apply(calc_next_calib, axis=1)

            edited_calib['검교정일자'] = edited_calib['검교정일자'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
            edited_calib['차기_검교정일자'] = edited_calib['차기_검교정일자'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else "")
            edited_calib['주기'] = edited_calib['주기'].apply(lambda x: str(int(x)) if pd.notna(x) else "")

            if calib_type_filter == "전체":
                edited_calib.to_csv(CALIB_LIST_FILE, index=False, encoding='utf-8-sig')
            else:
                other_df = df_calib[df_calib["구분"] != calib_type_filter]
                final_df = pd.concat([other_df, edited_calib], ignore_index=True)
                final_df.to_csv(CALIB_LIST_FILE, index=False, encoding='utf-8-sig')
            
            st.success("계측기기 검교정 대장이 성공적으로 저장되었습니다.")
            st.rerun()
            
    with tab2:
        st.write("자체 검교정 진행 시 성적서 데이터를 기록하고 보관합니다.")
        df_calib_rep = load_calib_reports()
        edited_calib_rep = st.data_editor(df_calib_rep, num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 자체 성적서 데이터 저장"):
            edited_calib_rep.to_csv(CALIB_REPORT_FILE, index=False, encoding='utf-8-sig')
            st.success("성적서 기록이 안전하게 저장되었습니다.")
            st.rerun()

# --- 10. HACCP 관리 메뉴 ---
elif menu_selection == "HACCP":
    if sub_menu == "HACCP 일지":
        st.markdown('<div class="section-title">🛡️ HACCP 일지 및 점검표 관리</div>', unsafe_allow_html=True)
        st.write("8대 분야별 HACCP 일지 및 점검표 양식을 업로드하고 관리할 수 있습니다.")

        # 8개 분류 탭 구성
        tabs = st.tabs([
            "1. 영업자 관리", "2. 위생관리", "3. 제조관리", "4. 용수관리", 
            "5. 보관운송관리", "6. 검사관리", "7. 회수관리", "8. HACCP"
        ])
        
        tab_names = ["1_영업자관리", "2_위생관리", "3_제조관리", "4_용수관리", "5_보관운송관리", "6_검사관리", "7_회수관리", "8_HACCP"]
        base_dir = "haccp_docs"
        os.makedirs(base_dir, exist_ok=True) # 폴더가 없으면 생성

        # 각 탭 안에 동일한 로직(업로드, 다운로드, 삭제) 반복
        for i, tab in enumerate(tabs):
            with tab:
                folder_name = os.path.join(base_dir, tab_names[i])
                os.makedirs(folder_name, exist_ok=True)
                
                st.markdown(f"#### 📂 {['영업자 관리', '위생관리', '제조관리', '용수관리', '보관운송관리', '검사관리', '회수관리', 'HACCP'][i]} 양식 관리")
                
                # 파일 업로더
                upl_file = st.file_uploader(f"새 문서 업로드", key=f"up_{i}", help="엑셀, 워드, 한글, PDF 등의 양식을 업로드하세요.")
                if upl_file:
                    file_path = os.path.join(folder_name, upl_file.name)
                    with open(file_path, "wb") as f:
                        f.write(upl_file.getbuffer())
                    st.success(f"'{upl_file.name}' 업로드 완료!")
                    st.rerun()
                
                st.markdown("##### 📄 등록된 문서 목록")
                files = os.listdir(folder_name)
                
                if not files:
                    st.info("등록된 문서가 없습니다.")
                else:
                    for f_name in files:
                        f_path = os.path.join(folder_name, f_name)
                        c_file, c_dl, c_del = st.columns([6, 1.5, 1.5])
                        
                        with c_file:
                            st.markdown(f"<div style='margin-top: 8px; font-weight:500;'>▪️ {f_name}</div>", unsafe_allow_html=True)
                            
                        with c_dl:
                            with open(f_path, "rb") as f_read:
                                st.download_button("📥 다운로드", data=f_read, file_name=f_name, key=f"dl_{i}_{f_name}", use_container_width=True)
                                
                        with c_del:
                            if st.button("🗑️ 삭제", key=f"del_{i}_{f_name}", use_container_width=True):
                                os.remove(f_path)
                                st.rerun()