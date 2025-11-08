import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import speech_recognition as sr
import os
import time
import io  # 👈 모바일 소리 에러 해결을 위한 핵심 도구!

# 👇 6번째 줄: Gemini 키를 넣어주세요!
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

st.set_page_config(page_title="대전 Easy-Tram", page_icon="🚃", layout="centered")
st.title("🚃 대전 Easy-Tram")
st.subheader("어르신, 궁금한 것을 찍어보세요")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# 🔊 AI가 말하게 하는 함수 (모바일 호환성 UP!)
def speak(text):
    try:
        tts = gTTS(text=text, lang='ko')
        # 파일을 만들지 않고 메모리에서 바로 재생 (에러 감소)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except Exception:
        st.warning("🔊 (죄송해유. 지금 핸드폰에서는 소리가 안 날 수도 있어유.)")

def listen_to_user():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        status = st.toast("👂 듣고 있어유... 말씀하셔유!")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            text = r.recognize_google(audio, language='ko-KR')
            return text
        except Exception:
            return None

def show_minwon_button():
    with st.expander("📞 그래도 궁금한 게 남으셨나요? (여기를 눌러보세요)"):
        st.write("AI 비서가 부족해서 죄송해요. 아래 버튼을 누르면 대전시 상담원(120)에게 바로 전화 연결됩니다.")
        st.link_button("👩‍💼 상담원에게 전화하기 (120)", "tel:120", use_container_width=True)

uploaded_file = st.file_uploader("사진 찍기", type=["jpg", "png", "jpeg"])

if uploaded_file:
    if st.session_state.uploaded_image != uploaded_file:
        st.session_state.chat_history = []
        st.session_state.uploaded_image = uploaded_file

    image = Image.open(uploaded_file)
    st.image(image, caption='찍은 사진')

    # --- [1차 분석] ---
    if not st.session_state.chat_history:
        with st.spinner('AI 비서가 사진을 보고 있습니다...'):
            try:
                prompt = """
                당신은 어르신을 위한 '교통 안내 비서'입니다.
                사진을 보고 핵심 내용을 쉬운 우리말 존댓말로 3~5문장으로 설명해주세요.
                "어르신," 하고 따뜻하게 부르며 시작하세요.
                (절대로 영어로 대답하지 마세요.)
                """
                response = model.generate_content([prompt, image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    # 대화 기록 표시
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "ai":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message['text'])
                # 마지막 답변에만 소리 재생기와 민원 버튼 달기
                if i == len(st.session_state.chat_history) - 1:
                     speak(message['text'])
                     show_minwon_button()
        else:
             with st.chat_message("user", avatar="👤"):
                st.write(message['text'])

    # --- [추가 질문 기능] ---
    st.write("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("궁금한 점을 적거나 마이크를 누르세요", key="user_input_box")
    with col2:
        if st.button("🎤 말하기"):
            voice_text = listen_to_user()
            if voice_text:
                st.session_state.chat_history.append({"role": "user", "text": voice_text})
                st.rerun()

    if user_input and st.button("질문 보내기"):
         st.session_state.chat_history.append({"role": "user", "text": user_input})
         st.rerun()

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner('답변을 생각 중입니다...'):
            try:
                last_question = st.session_state.chat_history[-1]["text"]
                follow_up_prompt = f"어르신 질문: '{last_question}'\n쉽고 친절하게 답변해주세요. (한국어만 사용)"
                response = model.generate_content([follow_up_prompt, image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")