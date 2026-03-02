# 🗳️ LivePoll - Mentimeter 클론 (Streamlit)

실시간 인터랙티브 투표 & 프레젠테이션 도구

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 앱 실행
```bash
streamlit run app.py
```

### 3. 접속 URL
| 역할 | URL |
|------|-----|
| 발표자 | `http://localhost:8501/?mode=presenter` |
| 참여자 | `http://localhost:8501/?mode=audience` |

---

## 📁 파일 구조

```
mentimeter_clone/
├── app.py          # 메인 진입점, 라우팅
├── db.py           # SQLite DB 관리 (CRUD, Lock)
├── presenter.py    # 발표자 UI & 시각화
├── audience.py     # 참여자 UI & 응답 폼
├── styles.css      # 다크 테마 커스텀 CSS
├── requirements.txt
└── responses.db    # 자동 생성됨
```

---

## 🎯 기능

### 발표자 모드 (`?mode=presenter`)
- ✅ 질문 유형 4가지: 객관식 / 단답형 / 워드클라우드 / 숫자 슬라이더
- ✅ 질문 활성화/비활성화 토글
- ✅ 실시간 Plotly 시각화 (2초 자동 갱신)
- ✅ 6자리 참여 코드 자동 생성
- ✅ QR코드 자동 생성
- ✅ 응답 초기화 기능

### 참여자 모드 (`?mode=audience`)
- ✅ 6자리 코드로 참여
- ✅ 모바일 반응형 UI
- ✅ 중복 제출 방지 (UUID 기반)
- ✅ 제출 완료 화면

---

## ☁️ Streamlit Cloud 배포

1. GitHub에 코드 업로드
2. [share.streamlit.io](https://share.streamlit.io) 에서 배포
3. `requirements.txt` 자동 감지

> **참고**: 클라우드 배포 시 SQLite는 서버 재시작마다 초기화됩니다.  
> 영구 저장이 필요하면 [Neon](https://neon.tech) 또는 [Supabase](https://supabase.com) PostgreSQL 사용 권장.

---

## 🔧 커스터마이징

### 자동 갱신 주기 변경 (`app.py`)
```python
refresh_interval = 2000  # 발표자: 2초 (ms)
refresh_interval = 3000  # 참여자: 3초 (ms)
```

### 한글 워드클라우드 설정 (`presenter.py`)
```python
# font_path에 한글 폰트 경로 지정
font_path="/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
```
