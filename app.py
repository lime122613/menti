"""
app.py - Mentimeter 클론 메인 진입점
실행: streamlit run app.py
URL: /?mode=presenter → 발표자 모드
     /?mode=audience  → 참여자 모드 (기본값)
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import db

# ────────────────────────────────────────────────────────────
# 페이지 기본 설정 (반드시 최상단에 위치)
# ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LivePoll | 실시간 인터랙티브 투표",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────────
# 커스텀 CSS 로드
# ────────────────────────────────────────────────────────────
def load_css():
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# ────────────────────────────────────────────────────────────
# DB 초기화 (앱 시작 시 1회)
# ────────────────────────────────────────────────────────────
db.init_db()

# ────────────────────────────────────────────────────────────
# URL 파라미터로 모드 결정
# ────────────────────────────────────────────────────────────
params = st.query_params
mode = params.get("mode", "audience").lower()

# ────────────────────────────────────────────────────────────
# 자동 새로고침 설정
# 발표자: 2초마다 / 참여자: 3초마다
# ────────────────────────────────────────────────────────────
refresh_interval = 2000 if mode == "presenter" else 3000
st_autorefresh(interval=refresh_interval, key=f"autorefresh_{mode}")

# ────────────────────────────────────────────────────────────
# 사이드바
# ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0;'>
        <div style='font-size:2.5rem;'>🗳️</div>
        <h2 style='color:#a78bfa; margin:0;'>LivePoll</h2>
        <p style='color:#6b7280; font-size:0.8rem; margin:0;'>실시간 인터랙티브 투표</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # 모드 전환 버튼
    current_mode_label = "🎙️ 발표자 모드" if mode == "presenter" else "👥 참여자 모드"
    st.markdown(f"**현재 모드:** {current_mode_label}")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎙️ 발표자", use_container_width=True):
            st.query_params["mode"] = "presenter"
            st.rerun()
    with col2:
        if st.button("👥 참여자", use_container_width=True):
            st.query_params["mode"] = "audience"
            st.rerun()

    st.divider()

    # 통계 요약
    st.markdown("**📈 현재 통계**")
    all_q = db.get_all_questions()
    active_q = db.get_active_question()

    st.markdown(f"""
    <div class='metric-card' style='margin-bottom:0.5rem;'>
        <div class='value' style='font-size:1.8rem;'>{len(all_q)}</div>
        <div class='label'>전체 질문</div>
    </div>""", unsafe_allow_html=True)

    if active_q:
        n = db.get_response_count(active_q["code"])
        st.markdown(f"""
        <div class='metric-card'>
            <div class='value' style='font-size:1.8rem; color:#38ef7d;'>{n}</div>
            <div class='label'>현재 질문 응답 수</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style='color:#6b7280; font-size:0.75rem; text-align:center;'>
        💡 발표자 URL: <code>?mode=presenter</code><br>
        💡 참여자 URL: <code>?mode=audience</code>
    </div>""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────
# 메인 헤더
# ────────────────────────────────────────────────────────────
if mode == "presenter":
    st.markdown("<h1>🗳️ LivePoll</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af; margin-top:-0.5rem;'>실시간 인터랙티브 프레젠테이션 도구</p>",
                unsafe_allow_html=True)
    st.divider()
else:
    st.markdown("<h1 style='text-align:center;'>🗳️ LivePoll</h1>", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────
# 모드별 렌더링
# ────────────────────────────────────────────────────────────
if mode == "presenter":
    from presenter import render_presenter
    render_presenter()
else:
    from audience import render_audience
    render_audience()
