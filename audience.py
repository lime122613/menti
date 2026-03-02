"""
audience.py - 참여자 모드 UI 모듈
"""

import streamlit as st
import uuid
import db


def ensure_user_id():
    """세션에 고유 사용자 ID 할당"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id


def render_audience():
    user_id = ensure_user_id()

    # ── 참여 코드 입력 화면 ──────────────────────
    if "audience_code" not in st.session_state or not st.session_state.audience_code:
        _render_code_input()
        return

    code = st.session_state.audience_code.strip().upper()
    q = db.get_question_by_code(code)

    # 코드 유효성 검사
    if not q:
        st.error("❌ 존재하지 않는 참여 코드입니다.")
        if st.button("다시 입력"):
            st.session_state.audience_code = ""
            st.rerun()
        return

    # 활성 질문 확인
    if not q["is_active"]:
        _render_waiting(q)
        return

    # 이미 응답한 경우
    if db.has_user_responded(code, user_id):
        _render_already_responded(q)
        return

    # 응답 폼
    _render_response_form(q, user_id)


# ──────────────────────────────────────────
# 서브 화면들
# ──────────────────────────────────────────

def _render_code_input():
    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem;'>
        <h2 style='color:#a78bfa; font-size:1.6rem;'>참여 코드를 입력하세요</h2>
        <p style='color:#9ca3af;'>발표자 화면에 표시된 6자리 코드를 입력하세요</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        code_input = st.text_input(
            "",
            max_chars=6,
            placeholder="예: AB12CD",
            label_visibility="collapsed"
        ).strip().upper()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 참여하기", use_container_width=True):
            if len(code_input) == 0:
                st.error("코드를 입력해주세요.")
            elif len(code_input) != 6:
                st.error("코드는 6자리여야 합니다.")
            else:
                st.session_state.audience_code = code_input
                st.rerun()

        st.markdown("""
        <br>
        <div style='text-align:center; color:#6b7280; font-size:0.85rem;'>
            📱 스마트폰에서도 참여 가능합니다
        </div>""", unsafe_allow_html=True)


def _render_waiting(q):
    """질문 대기 화면"""
    st.markdown(f"""
    <div style='text-align:center; padding:3rem 1rem;'>
        <div style='font-size:4rem; margin-bottom:1rem;'>⏳</div>
        <h3 style='color:#a78bfa;'>발표자의 질문을 기다리고 있습니다</h3>
        <p style='color:#9ca3af; font-size:0.9rem;'>참여 코드: <strong style='color:#667eea;'>{q['code']}</strong></p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🔙 코드 변경", use_container_width=True):
            st.session_state.audience_code = ""
            st.rerun()


def _render_already_responded(q):
    """이미 응답한 경우"""
    type_label = {"multiple": "객관식 투표", "short": "단답형",
                  "wordcloud": "워드클라우드", "slider": "숫자 슬라이더"}.get(
                      q["question_type"], "")
    st.markdown(f"""
    <div class='success-banner fade-in'>
        ✅ 응답이 완료되었습니다!<br>
        <span style='font-size:0.95rem; font-weight:400;'>결과는 발표자 화면에서 확인하세요</span>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align:center; padding:1.5rem; opacity:0.7;'>
        <p>질문: <em>{q['question_text']}</em></p>
        <p style='font-size:0.85rem; color:#9ca3af;'>유형: {type_label}</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다음 질문 기다리기", use_container_width=True):
            # 현재 코드 유지, 새로고침
            st.rerun()
    with col2:
        if st.button("🔙 처음으로", use_container_width=True):
            st.session_state.audience_code = ""
            if "submitted" in st.session_state:
                del st.session_state.submitted
            st.rerun()


def _render_response_form(q, user_id):
    """응답 입력 폼"""
    n_responses = db.get_response_count(q["code"])

    # 질문 카드
    type_icon = {"multiple": "📊", "short": "📝",
                 "wordcloud": "☁️", "slider": "🎚️"}.get(q["question_type"], "❓")
    st.markdown(f"""
    <div class='question-card fade-in'>
        <div style='color:#9ca3af; font-size:0.85rem; margin-bottom:0.5rem;'>
            {type_icon} 현재 질문 &nbsp;|&nbsp; 
            <span class='count-badge'>{n_responses}명 참여 중</span>
        </div>
        <div class='question-text'>{q['question_text']}</div>
    </div>""", unsafe_allow_html=True)

    answer = None

    # ── 객관식 ─────────────────────────────
    if q["question_type"] == "multiple":
        options = q.get("options", [])
        answer = st.radio(
            "답변을 선택하세요",
            options,
            index=None,
            label_visibility="collapsed"
        )

    # ── 단답형 ─────────────────────────────
    elif q["question_type"] == "short":
        answer = st.text_area(
            "답변을 입력하세요",
            placeholder="자유롭게 답변을 입력하세요...",
            height=120,
            label_visibility="collapsed"
        )

    # ── 워드클라우드 ───────────────────────
    elif q["question_type"] == "wordcloud":
        answer = st.text_input(
            "단어 또는 짧은 문장을 입력하세요",
            placeholder="예: 협업, 창의성, 도전...",
            label_visibility="collapsed"
        )
        st.caption("💡 여러 단어를 공백으로 구분해서 입력할 수 있어요")

    # ── 슬라이더 ──────────────────────────
    elif q["question_type"] == "slider":
        slider_val = st.slider(
            "값을 선택하세요",
            min_value=int(q.get("slider_min", 0)),
            max_value=int(q.get("slider_max", 100)),
            value=(int(q.get("slider_min", 0)) + int(q.get("slider_max", 100))) // 2,
            label_visibility="collapsed"
        )
        st.markdown(f"""
        <div style='text-align:center; font-size:3rem; font-weight:800; 
                    color:#667eea; margin:0.5rem 0;'>
            {slider_val}
        </div>""", unsafe_allow_html=True)
        answer = str(slider_val)

    # ── 제출 버튼 ──────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_disabled = False
        if q["question_type"] in ["multiple"] and not answer:
            submit_disabled = True
        if q["question_type"] in ["short", "wordcloud"] and (not answer or not answer.strip()):
            submit_disabled = True

        if st.button(
            "📤 제출하기",
            use_container_width=True,
            disabled=submit_disabled
        ):
            if answer is None or (isinstance(answer, str) and not answer.strip()):
                st.warning("답변을 입력해주세요.")
            else:
                final_answer = answer.strip() if isinstance(answer, str) else str(answer)
                success = db.submit_response(q["code"], user_id, final_answer)
                if success:
                    st.rerun()
                else:
                    st.error("제출 중 오류가 발생했습니다. 다시 시도해주세요.")

        if submit_disabled and q["question_type"] == "multiple":
            st.caption("☝️ 선택지를 먼저 선택해주세요")
