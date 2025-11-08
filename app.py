import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import os
import time
import io

# 👇 6번째 줄: Gemini API 키 다시 넣어주세요!
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

# 🔊 소리 재생 함수 (안정화 버전)
def speak(text):
    try:
        tts = gTTS(text=text, lang='ko')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', start_time=0)
    except Exception:
        st.warning("🔊 (소리 재생이 원활하지 않을 수 있어유)")

def show_minwon_button():
    with st.expander("📞 그래도 궁금한 게 남으셨나유?"):
        st.write("아래 버튼을 누르면 상담원(120)에게 바로 전화 연결됩니다.")
        st.link_button("👩‍💼 상담원 전화 연결 (120)", "tel:120", use_container_width=True)

# --- 메인 화면 ---
uploaded_file = st.file_uploader("사진 찍기", type=["jpg", "png", "jpeg"])

if uploaded_file:
    if st.session_state.uploaded_image != uploaded_file:
        st.session_state.chat_history = []
        st.session_state.uploaded_image = uploaded_file

    image = Image.open(uploaded_file)
    st.image(image, caption='찍은 사진')

    # [1차 분석]
    if not st.session_state.chat_history:
        with st.spinner('AI 비서가 분석 중입니다...'):
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
                st.error(f"오류가 발생했습니다: {e}")

    # 대화 기록 표시
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "ai":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message['text'])
                if i == len(st.session_state.chat_history) - 1:
                     speak(message['text'])
                     show_minwon_button()
        else:
             with st.chat_message("user", avatar="👤"):
                st.write(message['text'])

    # --- [질문 기능 (안정화 버전)] ---
    st.write("---")
    # 🎤 마이크 버튼을 삭제하고, 텍스트 입력창만 남겼습니다.
    # 대신 placeholder(안내 문구)에 팁을 적어줍니다.
    user_input = st.chat_input("궁금한 점을 적거나, 키보드의 마이크 버튼을 눌러 말씀해보세요")

    if user_input:
         st.session_state.chat_history.append({"role": "user", "text": user_input})
         with st.spinner('답변을 생각 중입니다...'):
            try:
                # 이전 대화 맥락을 포함해서 질문하기
                history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in st.session_state.chat_history[-3:]])
                follow_up_prompt = f"""
                [이전 대화]
                {history_text}
                
                [새로운 질문]
                어르신: {user_input}
                
                위 흐름을 보고 친절하게 쉬운 우리말로 답변해주세요.
                """
                response = model.generate_content([follow_up_prompt, image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")