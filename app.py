import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from gtts import gTTS
import io
import time

# --- [🔑 필수 설정] ---
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"  # 👇 6번째 줄: Gemini 키
WEATHER_API_KEY = "49271f92ea332122245325408c2ca765" # 👇 9번째 줄: 날씨 키

# --- [AI 설정] ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

# === 화면 설정 ===
st.set_page_config(page_title="대전 Easy-Tram", page_icon="🚃", layout="centered")

# --- [함수 모음] ---
def get_daejeon_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=36.35&lon=127.38&appid={WEATHER_API_KEY}&units=metric&lang=kr"
        response = requests.get(url).json()
        if response.get("weather"):
            desc = response["weather"][0]["description"]
            temp = round(response["main"]["temp"], 1)
            return f"{desc}, {temp}℃"
        else: return ""
    except: return ""

# 🔊 안정적인 소리 재생 함수 (메모리 스트리밍 방식)
def speak(text):
    try:
        tts = gTTS(text=text, lang='ko')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        # 바로 재생 시도 (iOS는 사용자가 재생 버튼을 눌러야 함)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except:
        pass # 에러 나도 조용히 넘어감

def show_minwon_button():
    with st.expander("📞 상담원 연결이 필요하신가요?"):
        st.link_button("👩‍💼 120 콜센터 전화하기", "tel:120", use_container_width=True)

# --- [기억 초기화] ---
if "mode" not in st.session_state: st.session_state.mode = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "uploaded_image" not in st.session_state: st.session_state.uploaded_image = None

# =========================================
# [화면 1] 모드 선택
# =========================================
if st.session_state.mode is None:
    st.title("🚃 대전 Easy-Tram")
    st.subheader("어떤 도움이 필요하신가요?")
    weather = get_daejeon_weather()
    if weather: st.info(f"🌤️ 현재 대전 날씨: **{weather}**")
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧳 대전 방문객\n(처음 왔어요)", use_container_width=True, type="primary"):
            st.session_state.mode = "visitor"
            st.rerun()
    with c2:
        if st.button("👴 어르신 도우미\n(쉽게 알려줘요)", use_container_width=True):
            st.session_state.mode = "senior"
            st.rerun()

# =========================================
# [화면 2] 메인 기능
# =========================================
else:
    if st.button("⬅️ 첫 화면으로 돌아가기"):
        st.session_state.mode = None
        st.session_state.chat_history = []
        st.rerun()

    if st.session_state.mode == "visitor":
        st.title("🧳 대전 여행 가이드")
        system_prompt = "당신은 '대전시 관광 홍보대사'입니다. 방문객에게 트램 이용법과 맛집/명소를 활기차게 추천해주세요."
    else:
        st.title("👴 어르신 교통 비서")
        system_prompt = "당신은 어르신을 위한 친절한 '교통 안내 비서'입니다. 쉬운 우리말 존댓말로 안전 정보를 최우선으로 설명해주세요."

    image = None
    uploaded_file = st.file_uploader("사진을 찍어보세요 (없어도 질문 가능)", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        if st.session_state.uploaded_image != uploaded_file:
            st.session_state.chat_history = []
            st.session_state.uploaded_image = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption='찍은 사진', use_container_width=True)

        # [사진 첫 분석]
        if not st.session_state.chat_history:
            with st.spinner('분석 중...'):
                try:
                    prompt = f"{system_prompt}\n이 사진을 보고 핵심 내용을 3~5문장으로 쉽게 설명해주세요."
                    response = model.generate_content([prompt, image])
                    st.session_state.chat_history.append({"role": "ai", "text": response.text})
                    st.rerun()
                except Exception as e: st.error("잠시 후 다시 시도해주세요.")

    # [대화 기록]
    for i, message in enumerate(st.session_state.chat_history):
        role = "assistant" if message["role"] == "ai" else "user"
        avatar = "🤖" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=avatar):
            st.write(message['text'])
            # 마지막 AI 답변에만 소리 재생기 표시
            if role == "assistant" and i == len(st.session_state.chat_history) - 1:
                speak(message['text'])
                if st.session_state.mode == "senior": show_minwon_button()

    # --- [안정적인 질문 기능] ---
    # 🎤 팁: 모바일에서는 키보드의 마이크 버튼을 누르면 음성 입력이 됩니다.
    user_input = st.chat_input("궁금한 점을 입력하세요 (키보드 마이크 사용 가능)")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        with st.spinner('답변 준비 중...'):
            try:
                history = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.chat_history[-3:]])
                prompt = f"{system_prompt}\n[이전 대화]{history}\n[새 질문]{user_input}\n친절하게 답변해주세요."
                if image: response = model.generate_content([prompt, image])
                else: response = model.generate_content(prompt)
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except: st.error("오류가 발생했습니다. 다시 질문해주세요.")