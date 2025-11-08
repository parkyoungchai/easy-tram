import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import speech_recognition as sr
import os
import time

# 👇 6번째 줄: Gemini 키를 넣어주세요!
GEMINI_API_KEY = "AIzaSyB-d0aIFMTsQQAsf0_Dm1qupfKOvRsKvo0"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

st.set_page_config(page_title="대전 Easy-Tram", page_icon="🚃", layout="centered")
st.title("🚃 대전 Easy-Tram")
st.subheader("어르신, 궁금한 것을 찍어보세요")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "processing" not in st.session_state:
    st.session_state.processing = False

def speak(text):
    try:
        tts = gTTS(text=text, lang='ko')
        filename = f"voice_{int(time.time())}.mp3"
        tts.save(filename)
        st.audio(filename, format="audio/mp3", start_time=0)
    except Exception:
        pass

def listen_to_user():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        status_placeholder = st.empty()
        status_placeholder.toast("👂 말씀해주세요... (듣고 있어요!)")
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            status_placeholder.toast("✅ 인식 중...")
            text = r.recognize_google(audio, language='ko-KR')
            return text
        except sr.WaitTimeoutError:
             status_placeholder.toast("⚠️ 아무 말도 안 들렸어요.")
             return None
        except sr.UnknownValueError:
             status_placeholder.toast("⚠️ 잘 못 알아들었어요. 다시 말씀해주세요.")
             return None
        except sr.RequestError:
             status_placeholder.toast("⚠️ 인터넷 연결을 확인해주세요.")
             return None

uploaded_file = st.file_uploader("사진 찍기", type=["jpg", "png", "jpeg"])

if uploaded_file:
    if st.session_state.uploaded_image != uploaded_file:
        st.session_state.chat_history = []
        st.session_state.uploaded_image = uploaded_file
        st.session_state.processing = False # 새 이미지 올리면 처리 상태 초기화

    image = Image.open(uploaded_file)
    st.image(image, caption='찍은 사진')

    # --- [1차 분석] ---
    if not st.session_state.chat_history and not st.session_state.processing:
        st.session_state.processing = True # 중복 실행 방지
        with st.spinner('AI 비서가 사진을 보고 있습니다...'):
            try:
                prompt = """
                당신은 어르신을 위한 '교통 안내 비서'입니다.
                사진을 보고 어르신이 꼭 아셔야 할 핵심 내용만 쉬운 우리말 존댓말로 설명해주세요.
                3~5문장 정도로 요약하고, "어르신," 하고 부르며 시작하세요.
                (절대로 영어로 대답하지 마세요.)
                """
                response = model.generate_content([prompt, image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.session_state.processing = False # 처리 완료
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")
                st.session_state.processing = False

    # 대화 기록 표시
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "ai":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message['text'])
                if i == len(st.session_state.chat_history) - 1:
                     speak(message['text'])
        else:
             with st.chat_message("user", avatar="👤"):
                st.write(message['text'])

    # --- [무한 질문 기능 (항상 떠있음)] ---
    st.write("---")
    
    # 1. 음성 입력 버튼 (항상 위에)
    if st.button("🎤 눌러서 말하기", use_container_width=True):
        voice_text = listen_to_user()
        if voice_text:
            st.session_state.chat_history.append({"role": "user", "text": voice_text})
            st.rerun()

    # 2. 텍스트 입력창 (항상 아래에)
    # 'st.chat_input'을 쓰면 엔터키 처리가 훨씬 매끄럽습니다!
    if user_input := st.chat_input("더 궁금한 점을 여기에 적어주세요"):
         st.session_state.chat_history.append({"role": "user", "text": user_input})
         st.rerun()

    # --- [AI 답변 생성 로직] ---
    # 가장 마지막 메시지가 '유저'의 질문이면 AI가 대답할 차례!
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner('답변을 생각 중입니다...'):
            try:
                last_question = st.session_state.chat_history[-1]["text"]
                
                # 이전 대화 기록을 어느 정도 기억하게 만들면 더 똑똑해집니다.
                history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in st.session_state.chat_history[-5:]])
                
                follow_up_prompt = f"""
                [이전 대화 기록]
                {history_text}
                
                [새로운 질문]
                어르신: {last_question}
                
                위 대화 흐름을 보고, 새로운 질문에 대해 쉽고 친절하게 답변해주세요. (한국어만 사용)
                """
                response = model.generate_content([follow_up_prompt, image])
                st.session_state.chat_history.append({"role": "ai", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")