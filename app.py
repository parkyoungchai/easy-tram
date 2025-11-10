import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import time
from gtts import gTTS
import io
import os
import pandas as pd
import numpy as np
from datetime import datetime

# --- [🔑 필수 설정: API 키 3개 입력] ---
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"      # 👇 6번째 줄: 구글 Gemini 키
WEATHER_API_KEY = "49271f92ea332122245325408c2ca765"  # 👇 9번째 줄: 날씨 API 키
TASHU_API_KEY = "apj2d20me6jch7sl"    # 👇 12번째 줄: 타슈 API 키

# --- [AI 설정] ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

# === 화면 설정 ===
st.set_page_config(page_title="대전 Easy-Tram", page_icon="🚃", layout="centered")

# 🔥 [CSS 디자인] 🔥
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    div.stButton > button {
        width: 100%; border-radius: 12px !important; height: 3.5em !important; font-weight: bold !important;
        border: 1px solid #ddd !important; transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #00C73C !important; border-color: #00C73C !important; color: white !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #009e2f !important; border-color: #009e2f !important;
    }
    div.stButton > button:has(div p:contains("방문객")) { background-color: #007BFF !important; color: white !important; }
    div.stButton > button:has(div p:contains("어르신")) { background-color: #FF4B4B !important; color: white !important; font-size: 1.3rem !important; }
    .stTextInput > div > div > input { border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- [함수 모음] ---
def get_daejeon_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=36.35&lon=127.38&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url, timeout=3).json()
        if response.get("weather"):
            desc = response["weather"][0]["description"]
            temp = round(response["main"]["temp"], 1)
            return f"{desc}, {temp}℃"
        return ""
    except: return ""

def speak(text):
    try:
        tts = gTTS(text=text, lang='ko')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except: pass

def show_minwon_button():
    with st.expander("📞 상담원 연결이 필요하신가요?"):
        st.link_button("👩‍💼 120 상담원 전화하기", "tel:120", use_container_width=True)

def ask_ai_with_retry(content, retries=3):
    last_error = None
    for _ in range(retries):
        try:
            return model.generate_content(content)
        except Exception as e:
            last_error = e
            time.sleep(1)
    raise last_error

def get_mock_tashu_data():
    data = {'lat': [36.3504, 36.3587, 36.3325, 36.3615, 36.3284], 'lon': [127.3845, 127.3848, 127.4342, 127.3546, 127.4213], 'station': ['(예시) 대전시청', '(예시) 정부청사', '(예시) 대전역', '(예시) 유성온천', '(예시) 중앙로'], 'bikes': np.random.randint(3, 15, 5)}
    return pd.DataFrame(data)

def get_real_tashu_data():
    URL = f"http://apis.data.go.kr/6300000/Tashu/getStationList?serviceKey={TASHU_API_KEY}&pageNo=1&numOfRows=500&type=json"
    try:
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                df = pd.DataFrame(items)
                df = df.rename(columns={'Y_POS': 'lat', 'X_POS': 'lon', 'STATION_NAME': 'station', 'PARKING_COUNT': 'bikes'})
                df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                return df.dropna(subset=['lat', 'lon'])
        return get_mock_tashu_data()
    except: return get_mock_tashu_data()

# --- [기억 초기화] ---
if "mode" not in st.session_state: st.session_state.mode = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None
if "show_tashu" not in st.session_state: st.session_state.show_tashu = False

# =========================================
# [화면 1] 모드 선택
# =========================================
if st.session_state.mode is None:
    # 🚨 [수정됨] 변수 이름을 c1, c2, c3, c4로 통일했습니다!
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1: st.title("대전 Easy-Tram")
    with c2:
        if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", use_container_width=True)
    with c3:
        if os.path.exists("한화이글스.jpg"): st.image("한화이글스.jpg", use_container_width=True)
    with c4:
        if os.path.exists("성심당.jpg"): st.image("성심당.jpg", use_container_width=True)

    # 피드백 버튼
    with st.expander("💬 피드백 및 건의사항 보내기"):
        feedback = st.text_area("더 좋은 서비스를 위해 의견을 남겨주세요!", height=100)
        if st.button("의견 보내기"):
            if feedback:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("feedback.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{now}] {feedback}\n")
                st.success("소중한 의견 감사합니다!")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("내용을 입력해주세요.")

    st.subheader("반갑습니다! 어떤 도움이 필요하신가요?")
    weather = get_daejeon_weather()
    if weather: st.info(f"🌤️ 현재 대전 날씨: **{weather}**")
    st.write("---")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧳 대전 방문객\n(처음 왔어요)", use_container_width=True):
            st.session_state.mode = "visitor"
            st.rerun()
    with c2:
        if st.button("👴 어르신 도우미\n(쉽게 알려줘요)", use_container_width=True):
            st.session_state.mode = "senior"
            st.rerun()

    st.write("")
    if st.button("🚲 내 주변 '타슈' 찾기 (지도 보기)", use_container_width=True, type="primary"):
        st.session_state.show_tashu = not st.session_state.show_tashu

    if st.session_state.show_tashu:
        with st.spinner("🚲 타슈 위치를 찾는 중..."):
            tashu_df = get_real_tashu_data()
        if '(예시)' in tashu_df['station'].iloc[0]:
             st.warning("⚠️ 현재 '시뮬레이션 데이터'를 보여줍니다.")
        else:
             st.success(f"✅ 실시간 타슈 {len(tashu_df)}곳을 찾았습니다!")
        tashu_df['color'] = '#00C73C'
        st.map(tashu_df, latitude='lat', longitude='lon', size=40, color='color')
        with st.expander("📋 대여소별 잔여 대수 보기"):
             st.dataframe(tashu_df[['station', 'bikes']].rename(columns={'station':'대여소명', 'bikes':'잔여대수'}), hide_index=True, use_container_width=True)
        st.write("---")

# =========================================
# [화면 2] 메인 기능
# =========================================
else:
    if st.session_state.mode == "senior":
        st.markdown("""<style> p, div, button, input { font-size: 1.3rem !important; } </style>""", unsafe_allow_html=True)

    if st.button("⬅️ 첫 화면"):
        st.session_state.mode = None
        st.session_state.show_tashu = False
        st.session_state.chat_history = []
        st.rerun()

    if st.session_state.mode == "visitor":
        st.title("🧳 대전 여행 가이드")
        system_prompt = "당신은 '대전시 관광 홍보대사'입니다. 방문객에게 트램 이용법과 맛집/명소를 활기차게 추천해주세요."
    else:
        c1, c2 = st.columns([3, 1])
        with c1: st.title("👴 어르신 교통 비서")
        with c2:
             if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", width=80)
        system_prompt = "당신은 대전의 마스코트 '꿈돌이'입니다. 어르신을 위해 쉽고 천천히 설명해주세요."

    image = None
    uploaded_file = st.file_uploader("사진을 찍어보세요 (없어도 질문 가능)", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        if st.session_state.uploaded_image != uploaded_file:
            st.session_state.chat_history = []
            st.session_state.uploaded_image = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption='찍은 사진', use_column_width=True)

        if not st.session_state.chat_history:
            with st.spinner('분석 중...'):
                try:
                    prompt = f"{system_prompt}\n이 사진을 보고 핵심 내용을 문장으로 아주 쉽게 설명해주세요."
                    response = ask_ai_with_retry([prompt, image])
                    st.session_state.chat_history.append({"role": "ai", "text": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"🚨 에러 발생: {e}")

    for i, message in enumerate(st.session_state.chat_history):
        role = "assistant" if message["role"] == "ai" else "user"
        avatar = "🤖"
        if st.session_state.mode == "senior" and role == "assistant":
             if os.path.exists("꿈돌이.jpg"): avatar = "꿈돌이.jpg"
             else: avatar = "🟡"
        with st.chat_message(role, avatar=avatar):
            st.write(message['text'])
            if role == "assistant" and i == len(st.session_state.chat_history) - 1:
                speak(message['text'])
                if st.session_state.mode == "senior": show_minwon_button()

    user_input = st.chat_input("궁금한 점을 입력하세요 (키보드 마이크 사용 가능)")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner('생각 중...'):
            try:
                history = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.chat_history[-3:]])
                prompt = f"{system_prompt}\n[이전 대화]{history}\n[새 질문]{user_input}\n친절하게 답변해주세요."
                if image: response = ask_ai_with_retry([prompt, image])
                else: response = ask_ai_with_retry(prompt)
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"🚨 에러 발생: {e}")