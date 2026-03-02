"""
presenter.py - 발표자 모드 UI 모듈
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import io
import base64
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

import db


# ──────────────────────────────────────────
# 시각화 함수
# ──────────────────────────────────────────

def render_multiple_choice_chart(responses, options):
    """객관식 응답 가로 막대 그래프"""
    counts = Counter([r["answer"] for r in responses])
    data = {opt: counts.get(opt, 0) for opt in options}
    total = sum(data.values())

    df = pd.DataFrame({
        "선택지": list(data.keys()),
        "응답 수": list(data.values()),
        "비율(%)": [round(v / total * 100, 1) if total > 0 else 0 for v in data.values()]
    })
    df = df.sort_values("응답 수", ascending=True)

    fig = px.bar(
        df, x="응답 수", y="선택지", orientation="h",
        text=df.apply(lambda r: f"{int(r['응답 수'])}명 ({r['비율(%)']:.1f}%)", axis=1),
        color="응답 수",
        color_continuous_scale=["#667eea", "#764ba2", "#f093fb"],
    )
    fig.update_traces(textposition="outside", textfont_size=14)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#e0e0e0", size=13),
        showlegend=False,
        coloraxis_showscale=False,
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        margin=dict(l=10, r=80, t=30, b=10),
        height=max(300, len(options) * 60 + 80),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_slider_chart(responses):
    """숫자 응답 히스토그램 + 평균/중앙값"""
    values = []
    for r in responses:
        try:
            values.append(float(r["answer"]))
        except:
            pass

    if not values:
        st.info("📊 아직 응답이 없습니다.")
        return

    df = pd.DataFrame({"값": values})
    avg = sum(values) / len(values)
    median = sorted(values)[len(values) // 2]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='value'>{avg:.1f}</div>
            <div class='label'>평균</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='value'>{median:.0f}</div>
            <div class='label'>중앙값</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='value'>{len(values)}</div>
            <div class='label'>응답 수</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig = px.histogram(
        df, x="값", nbins=20,
        color_discrete_sequence=["#667eea"],
    )
    fig.add_vline(x=avg, line_dash="dash", line_color="#f093fb",
                  annotation_text=f"평균 {avg:.1f}", annotation_font_color="#f093fb")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#e0e0e0", size=13),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="빈도"),
        margin=dict(l=10, r=10, t=30, b=10),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)


def get_korean_font_path() -> str | None:
    """한글 폰트 경로 반환 - 없으면 자동 다운로드"""
    import os, urllib.request

    # 1순위: Streamlit Cloud / Ubuntu 나눔폰트
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        # Windows
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    # 2순위: 로컬 캐시에 다운로드
    local_path = "/tmp/NanumGothic.ttf"
    if os.path.exists(local_path):
        return local_path

    try:
        url = (
            "https://github.com/google/fonts/raw/main/ofl/"
            "nanumgothic/NanumGothic-Regular.ttf"
        )
        urllib.request.urlretrieve(url, local_path)
        return local_path
    except Exception:
        return None


def render_wordcloud(responses):
    """워드클라우드 시각화 (한글 지원)"""
    texts = " ".join([r["answer"] for r in responses if r["answer"].strip()])
    if not texts.strip():
        st.info("💬 아직 응답이 없습니다.")
        return

    font_path = get_korean_font_path()

    try:
        wc = WordCloud(
            width=900, height=450,
            background_color=None, mode="RGBA",
            colormap="cool",
            max_words=80,
            prefer_horizontal=0.7,
            font_path=font_path,   # 한글 폰트 자동 적용
            collocations=False,
        )
        wc.generate(texts)
        fig, ax = plt.subplots(figsize=(9, 4.5))
        fig.patch.set_alpha(0)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight",
                    transparent=True, dpi=150)
        plt.close(fig)
        buf.seek(0)
        st.image(buf, use_container_width=True)

        if not font_path:
            st.caption("⚠️ 한글 폰트를 불러오지 못했습니다. 아래 단어 빈도 차트를 참고하세요.")
            raise Exception("no font")

    except Exception:
        # 폴백: 단어 빈도 가로 막대 차트
        words = texts.split()
        word_counts = Counter(words).most_common(15)
        if word_counts:
            df = pd.DataFrame(word_counts, columns=["단어", "빈도"])
            fig = px.bar(df, x="빈도", y="단어", orientation="h",
                         color="빈도",
                         color_continuous_scale=["#667eea", "#f093fb"])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.03)",
                font=dict(color="#e0e0e0"),
                showlegend=False, coloraxis_showscale=False,
                height=400, margin=dict(l=10, r=30, t=20, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)


def render_short_answer(responses):
    """단답형 응답 카드 리스트"""
    if not responses:
        st.info("📝 아직 응답이 없습니다.")
        return

    # 최신순 정렬
    sorted_resp = sorted(responses, key=lambda x: x["submitted_at"], reverse=True)
    for r in sorted_resp[:50]:  # 최대 50개 표시
        st.markdown(f"""
        <div class='response-card'>
            💬 {r['answer']}
        </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# QR코드 생성
# ──────────────────────────────────────────

def generate_qr_code(url: str) -> str:
    """QR코드 생성 후 base64 반환"""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8, border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#667eea", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception:
        return None


# ──────────────────────────────────────────
# 발표자 메인 UI
# ──────────────────────────────────────────

def render_presenter():
    st.markdown("## 🎙️ 발표자 대시보드")

    # 탭 구성
    tab_create, tab_manage, tab_live = st.tabs(["➕ 질문 만들기", "📋 질문 관리", "📊 실시간 결과"])

    # ── 탭 1: 질문 만들기 ──────────────────
    with tab_create:
        st.markdown("### 새 질문 추가")

        q_type = st.selectbox(
            "질문 유형", 
            ["multiple", "short", "wordcloud", "slider"],
            format_func=lambda x: {
                "multiple": "📊 객관식 투표",
                "short": "📝 단답형",
                "wordcloud": "☁️ 워드클라우드",
                "slider": "🎚️ 숫자 슬라이더"
            }[x]
        )

        q_text = st.text_area(
            "질문 내용 *",
            placeholder="예) 오늘 강의에서 가장 인상 깊었던 것은?",
            height=100
        )

        options = None
        slider_min, slider_max = 0, 100

        if q_type == "multiple":
            st.markdown("**선택지 입력** (한 줄에 하나씩)")
            raw = st.text_area(
                "", 
                placeholder="선택지 1\n선택지 2\n선택지 3",
                height=120,
                label_visibility="collapsed"
            )
            options = [o.strip() for o in raw.strip().split("\n") if o.strip()]
            if options:
                st.caption(f"✅ 선택지 {len(options)}개 인식됨: {', '.join(options)}")

        elif q_type == "slider":
            col1, col2 = st.columns(2)
            with col1:
                slider_min = st.number_input("최솟값", value=0, step=1)
            with col2:
                slider_max = st.number_input("최댓값", value=100, step=1)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 질문 생성", use_container_width=True):
            if not q_text.strip():
                st.error("질문 내용을 입력해주세요.")
            elif q_type == "multiple" and (not options or len(options) < 2):
                st.error("객관식 선택지를 2개 이상 입력해주세요.")
            else:
                code = db.create_question(
                    q_text.strip(), q_type, options, slider_min, slider_max
                )
                st.success(f"✅ 질문이 생성됐습니다! 참여 코드: **{code}**")
                st.rerun()

    # ── 탭 2: 질문 관리 ──────────────────
    with tab_manage:
        st.markdown("### 질문 목록")
        questions = db.get_all_questions()

        if not questions:
            st.info("아직 생성된 질문이 없습니다. '질문 만들기' 탭에서 추가하세요.")
        else:
            active = db.get_active_question()
            active_code = active["code"] if active else None

            for q in questions:
                is_active = q["code"] == active_code
                with st.container():
                    col1, col2, col3 = st.columns([5, 2, 1])
                    with col1:
                        type_icon = {"multiple": "📊", "short": "📝",
                                     "wordcloud": "☁️", "slider": "🎚️"}.get(q["question_type"], "❓")
                        status = "🟢 **활성**" if is_active else "⚪ 대기중"
                        n = db.get_response_count(q["code"])
                        st.markdown(f"""
                        {type_icon} **{q['question_text'][:60]}**  
                        코드: `{q['code']}` | 응답: {n}명 | {status}
                        """)
                    with col2:
                        if is_active:
                            if st.button("⏹ 비활성화", key=f"deact_{q['code']}"):
                                db.set_active_question(None)
                                st.rerun()
                        else:
                            if st.button("▶ 활성화", key=f"act_{q['code']}"):
                                db.set_active_question(q["code"])
                                st.rerun()
                    with col3:
                        if st.button("🗑", key=f"del_{q['code']}",
                                     help="질문 삭제"):
                            db.delete_question(q["code"])
                            st.rerun()
                    st.divider()

    # ── 탭 3: 실시간 결과 ──────────────────
    with tab_live:
        active_q = db.get_active_question()

        if not active_q:
            st.markdown("""
            <div style='text-align:center; padding: 3rem; opacity:0.6;'>
                <h3>📭 활성화된 질문이 없습니다</h3>
                <p>'질문 관리' 탭에서 질문을 활성화하세요.</p>
            </div>""", unsafe_allow_html=True)
            return

        responses = db.get_responses(active_q["code"])
        n = len(responses)

        # 헤더
        col_info, col_code = st.columns([3, 2])
        with col_info:
            type_label = {"multiple": "객관식 투표", "short": "단답형",
                          "wordcloud": "워드클라우드", "slider": "숫자 슬라이더"}.get(
                              active_q["question_type"], "")
            st.markdown(f"**{active_q['question_text']}**")
            st.markdown(f"""
            <span class='count-badge'>N = {n}명 응답</span>&nbsp;
            <small style='color:#9ca3af'>유형: {type_label}</small>
            """, unsafe_allow_html=True)

            # 응답 초기화 버튼
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 응답 초기화", help="현재 질문의 모든 응답을 삭제합니다"):
                db.clear_responses(active_q["code"])
                st.rerun()

        with col_code:
            # QR코드 + 참여 코드
            audience_url = "https://livepoll.streamlit.app/?mode=audience"
            qr_b64 = generate_qr_code(audience_url)
            
            st.markdown(f"""
            <div class='code-display'>
                <div class='code-label'>참여 코드</div>
                <div class='code-text'>{active_q['code']}</div>
            </div>""", unsafe_allow_html=True)

            if qr_b64:
                st.image(f"data:image/png;base64,{qr_b64}",
                         caption="QR코드로 참여", width=160)

        st.divider()

        # 시각화
        q_type = active_q["question_type"]
        if q_type == "multiple":
            render_multiple_choice_chart(responses, active_q.get("options", []))
        elif q_type == "slider":
            render_slider_chart(responses)
        elif q_type == "wordcloud":
            render_wordcloud(responses)
        elif q_type == "short":
            render_short_answer(responses)
