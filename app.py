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

# --- [🔑 필수 설정: API 키 4개 입력!] ---
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"      # 👇 Gemini 키
WEATHER_API_KEY = "49271f92ea332122245325408c2ca765"  # 👇 날씨 키
TASHU_API_KEY = "apj2d20me6jch7sl"    # 👇 타슈 키
SHEETDB_URL = "https://sheetdb.io/api/v1/YOUR_API_KEY" # 👇 SheetDB URL

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
    .stSelectbox div[data-testid="stSelectboxInline"] { max-width: 150px; font-size: 0.9em; }
    </style>
""", unsafe_allow_html=True)

# --- [다국어 텍스트 & 스마트 프롬프트] ---
TEXTS = {
    "ko": {
        "welcome": "반갑습니다! 어떤 도움이 필요하신가요?",
        "feedback_title": "💬 피드백 및 건의사항 보내기",
        "feedback_placeholder": "더 좋은 서비스를 위해 의견을 남겨주세요!",
        "feedback_button": "의견 보내기",
        "feedback_success": "✅ 소중한 의견이 안전하게 저장되었습니다!",
        "feedback_fail": "저장 실패. 다시 시도해주세요.",
        "weather_prefix": "🌤️ 현재 대전 날씨:",
        "visitor_button": "🧳 대전 방문객\n(처음 왔어요)",
        "senior_button": "👴 어르신 도우미\n(쉽게 알려줘요)",
        "tashu_button": "🚲 내 주변 '타슈' 찾기 (지도 보기)",
        "tashu_loading": "🚲 타슈 위치를 찾는 중...",
        "tashu_success": "✅ 실시간 타슈 {count}곳을 찾았습니다!",
        "tashu_expander": "📋 대여소별 잔여 대수 보기",
        "back_to_home": "⬅️ 첫 화면",
        "visitor_title": "🧳 대전 여행 가이드",
        "senior_title": "👴 어르신 교통 비서",
        "photo_uploader": "사진을 찍어보세요 (없어도 질문 가능)",
        "photo_caption": "찍은 사진",
        "analyzing": "분석 중...",
        "ai_error": "🚨 에러 발생:",
        "chat_input_placeholder": "궁금한 점을 입력하세요 (키보드 마이크 사용 가능)",
        "thinking": "생각 중...",
        "ai_explain_image": "이 사진을 보고 핵심 내용을 3문장으로 아주 쉽게 설명해주세요.",
        "ai_chat_reply": "친절하게 답변해주세요.",
        "call_center_expander": "📞 상담원 연결이 필요하신가요?",
        "call_center_button": "👩‍💼 120 콜센터 전화하기",
        "tashu_station_col": "대여소명",
        "tashu_bikes_col": "잔여대수",
        "tashu_mock_warning": "⚠️ 현재 '시뮬레이션 데이터'를 보여줍니다.",
        # 🚨 [수정] 15분 이상 걸릴 때만 추천하도록 변경!
        "visitor_prompt": "당신은 '대전시 관광 홍보대사'입니다. 방문객에게 트램 이용법과 맛집을 추천해주세요. [중요] 목적지까지 도보로 15분 이상 걸릴 것 같을 때만 '타슈(공영자전거)' 이용을 추천해주세요.",
        "senior_prompt": "당신은 대전의 마스코트 '꿈돌이'입니다. 어르신께 쉬운 우리말로 천천히 설명해주세요. [중요] 걷기에 조금 먼 거리(15분 이상)라면, 힘들지 않게 '타슈(자전거)'를 타보시라고 권유해주세요. 답변은 \"어르신,\" 하고 시작하세요."
    },
    "en": {
        "welcome": "Hello! How can I help you?",
        "feedback_title": "💬 Send Feedback",
        "feedback_placeholder": "Please share your thoughts!",
        "feedback_button": "Send",
        "feedback_success": "✅ Feedback saved securely!",
        "feedback_fail": "Failed to save.",
        "weather_prefix": "🌤️ Current Weather:",
        "visitor_button": "🧳 Visitor\n(First time)",
        "senior_button": "👴 Senior\n(Easy mode)",
        "tashu_button": "🚲 Find 'Tashu' nearby",
        "tashu_loading": "🚲 Searching...",
        "tashu_success": "✅ Found {count} stations!",
        "tashu_expander": "📋 View details",
        "back_to_home": "⬅️ Home",
        "visitor_title": "🧳 Travel Guide",
        "senior_title": "👴 Senior Helper",
        "photo_uploader": "Take a photo",
        "photo_caption": "Uploaded Photo",
        "analyzing": "Analyzing...",
        "ai_error": "🚨 Error:",
        "chat_input_placeholder": "Ask anything",
        "thinking": "Thinking...",
        "ai_explain_image": "Explain this photo in 3 simple sentences.",
        "ai_chat_reply": "Please reply kindly.",
        "call_center_expander": "📞 Need help?",
        "call_center_button": "👩‍💼 Call Center (120)",
        "tashu_station_col": "Station Name",
        "tashu_bikes_col": "Bikes",
        "tashu_mock_warning": "⚠️ Showing simulation data.",
        # 🚨 [수정] 영어 프롬프트도 15분 조건 추가
        "visitor_prompt": "You are a 'Daejeon Tourism Ambassador'. Recommend tram usage and spots. [Important] Only recommend 'Tashu' (public bike) if the destination is more than a 15-minute walk away.",
        "senior_prompt": "You are 'Kkumdori'. Explain simply and slowly for seniors. [Important] If the walk seems long (over 15 mins), suggest using 'Tashu' for ease."
    },
    # (다른 언어는 공간상 생략했지만, 동일한 방식으로 수정하면 됩니다.)
}

# --- [함수 모음] ---
def get_daejeon_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=36.35&lon=127.38&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url, timeout=3).json()
        if response.get("weather"):
            return f"{response['weather'][0]['description']}, {round(response['main']['temp'], 1)}℃"
        return ""
    except: return ""

def speak(text, lang='ko'):
    try:
        tts = gTTS(text=text, lang=lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except: pass

def show_minwon_button(texts):
    with st.expander(texts["call_center_expander"]):
        st.link_button(texts["call_center_button"], "tel:120", use_container_width=True)

def ask_ai_with_retry(content, retries=3):
    for _ in range(retries):
        try: return model.generate_content(content)
        except: time.sleep(1)
    raise Exception("AI 응답 없음")

def get_mock_tashu_data():
    data = {'lat': [36.3504, 36.3587, 36.3325, 36.3615, 36.3284], 'lon': [127.3845, 127.3848, 127.4342, 127.3546, 127.4213], 'station': ['(예시)시청', '(예시)정부청사', '(예시)대전역', '(예시)유성온천', '(예시)중앙로'], 'bikes': np.random.randint(3, 15, 5)}
    return pd.DataFrame(data)

def get_real_tashu_data():
    try:
        url = f"http://apis.data.go.kr/6300000/Tashu/getStationList?serviceKey={TASHU_API_KEY}&pageNo=1&numOfRows=500&type=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                df = pd.DataFrame(items)
                df = df.rename(columns={'Y_POS': 'lat', 'X_POS': 'lon', 'STATION_NAME': 'station', 'PARKING_COUNT': 'bikes'})
                df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                return df.dropna(subset=['lat', 'lon'])
    except: pass
    return get_mock_tashu_data()

def save_to_google_sheet(feedback_text):
    try:
        requests.post(SHEETDB_URL, json={"data": {"날짜시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "내용": feedback_text}})
        return True
    except: return False

# --- [초기화] ---
if "mode" not in st.session_state: st.session_state.mode = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None
if "show_tashu" not in st.session_state: st.session_state.show_tashu = False
if "lang" not in st.session_state: st.session_state.lang = "ko"

t = TEXTS.get(st.session_state.lang, TEXTS["ko"])

# =========================================
# [화면 1] 모드 선택
# =========================================
if st.session_state.mode is None:
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1: st.title("대전 Easy-Tram")
    with c2:
        if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", use_container_width=True)
    with c3:
        if os.path.exists("한화이글스.jpg"): st.image("한화이글스.jpg", use_container_width=True)
    with c4:
        if os.path.exists("성심당.jpg"): st.image("성심당.jpg", use_container_width=True)

    with st.expander(t["feedback_title"]):
        feedback = st.text_area(t["feedback_placeholder"], height=100)
        if st.button(t["feedback_button"]):
            if feedback:
                save_to_google_sheet(feedback)
                with open("feedback.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] {feedback}\n")
                st.success(t["feedback_success"])
                time.sleep(1)
                st.rerun()

    c_sub, c_lang = st.columns([4, 1])
    with c_sub: st.subheader(t["welcome"])
    with c_lang:
        sel_lang = st.selectbox("", ["한국어", "English"], index=0 if st.session_state.lang == "ko" else 1, label_visibility="collapsed")
        if (sel_lang == "한국어" and st.session_state.lang != "ko") or (sel_lang == "English" and st.session_state.lang != "en"):
            st.session_state.lang = "ko" if sel_lang == "한국어" else "en"
            st.rerun()

    weather = get_daejeon_weather()
    if weather: st.info(f"{t['weather_prefix']} **{weather}**")
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t["visitor_button"], use_container_width=True):
            st.session_state.mode = "visitor"
            st.rerun()
    with c2:
        if st.button(t["senior_button"], use_container_width=True):
            st.session_state.mode = "senior"
            st.rerun()
    st.write("")
    if st.button(t["tashu_button"], use_container_width=True, type="primary"):
        st.session_state.show_tashu = not st.session_state.show_tashu
    if st.session_state.show_tashu:
        with st.spinner(t["tashu_loading"]):
            tashu_df = get_real_tashu_data()
        if '(예시)' in tashu_df['station'].iloc[0]:
             st.warning(t["tashu_mock_warning"])
        else:
             st.success(t["tashu_success"].format(count=len(tashu_df)))
        tashu_df['color'] = '#00C73C'
        st.map(tashu_df, latitude='lat', longitude='lon', size=40, color='color')
        with st.expander(t["tashu_expander"]):
             st.dataframe(tashu_df[['station', 'bikes']].rename(columns={'station':t["tashu_station_col"], 'bikes':t["tashu_bikes_col"]}), hide_index=True, use_container_width=True)
        st.write("---")

# =========================================
# [화면 2] 메인 기능
# =========================================
else:
    if st.session_state.mode == "senior":
        st.markdown("""<style> p, div, button, input { font-size: 1.3rem !important; } </style>""", unsafe_allow_html=True)

    if st.button(t["back_to_home"]):
        st.session_state.mode = None
        st.session_state.show_tashu = False
        st.session_state.chat_history = []
        st.rerun()

    if st.session_state.mode == "visitor":
        st.title(t["visitor_title"])
        system_prompt = t["visitor_prompt"]
    else:
        c1, c2 = st.columns([3, 1])
        with c1: st.title(t["senior_title"])
        with c2:
             if os.path.exists("꿈돌이.jpg"): st.image("꿈돌이.jpg", width=80)
        system_prompt = t["senior_prompt"]

    uploaded_file = st.file_uploader(t["photo_uploader"], type=["jpg", "png", "jpeg"])
    if uploaded_file:
        if st.session_state.uploaded_image != uploaded_file:
            st.session_state.chat_history = []
            st.session_state.uploaded_image = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption=t.get("photo_caption", "사진"), use_container_width=True)
        if not st.session_state.chat_history:
            with st.spinner(t["analyzing"]):
                try:
                    prompt = f"{system_prompt}\n{t['ai_explain_image']}"
                    response = ask_ai_with_retry([prompt, image])
                    st.session_state.chat_history.append({"role": "ai", "text": response.text})
                    st.rerun()
                except Exception as e: st.error(f"{t['ai_error']} {e}")

    for i, message in enumerate(st.session_state.chat_history):
        role = "assistant" if message["role"] == "ai" else "user"
        avatar = "🤖"
        if st.session_state.mode == "senior" and role == "assistant":
             if os.path.exists("꿈돌이.jpg"): avatar = "꿈돌이.jpg"
             else: avatar = "🟡"
        with st.chat_message(role, avatar=avatar):
            st.write(message['text'])
            if role == "assistant" and i == len(st.session_state.chat_history) - 1:
                speak(message['text'], lang=st.session_state.lang)
                if st.session_state.mode == "senior": show_minwon_button(t)

    user_input = st.chat_input(t["chat_input_placeholder"])
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner(t["thinking"]):
            try:
                history = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.chat_history[-3:]])
                prompt = f"{system_prompt}\n[이전 대화]{history}\n[새 질문]{user_input}\n{t['ai_chat_reply']}"
                if 'image' in locals() and image: response = ask_ai_with_retry([prompt, image])
                else: response = ask_ai_with_retry(prompt)
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e: st.error(f"{t['ai_error']} {e}")