import streamlit as st
import pandas as pd
import random
from openai import OpenAI
import os

# ✅ OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 데이터 로드
df = pd.read_excel("태그_날짜_날씨_추가된_메시지.xlsx", sheet_name="전체")

# 태그, 톤, 유형 후보 수집
tag_options = sorted({tag for sublist in df['태그'].dropna().apply(eval) for tag in sublist})
tone_options = ["응원", "공지", "피드백"]
type_options = df['유형'].dropna().unique().tolist()
weather_options = ["맑음", "비", "눈", "폭우", "폭설", "폭염"]
holiday_options = ["평일", "주말", "공휴일", "설날", "추석"]

st.title("🧠 GPT 기반 자동 메시지 생성기")

# 사용자 입력
selected_tags = st.multiselect("강조할 태그를 선택하세요", tag_options)
selected_tone = st.selectbox("메시지 톤을 선택하세요", tone_options)
selected_type = st.selectbox("메시지 유형을 선택하세요", type_options)
selected_weather = st.selectbox("해당 날씨를 선택하세요", weather_options)
selected_holiday = st.selectbox("해당 날짜 정보를 선택하세요", holiday_options)

# 날씨 및 명절 보정 문구 사전
def get_weather_phrase(weather):
    return {
        "눈": "눈길에는 감속과 안전운전이 무엇보다 중요합니다.",
        "비": "비 오는 날에는 부드러운 제동과 속도 유지에 유의해주세요.",
        "폭염": "폭염 속에는 차량 상태와 냉방 점검도 중요합니다.",
        "폭우": "폭우 시에는 감속과 저속 운전이 필수입니다.",
        "폭설": "폭설에는 제동 거리 확보에 특히 주의해주세요.",
    }.get(weather, "")

def get_holiday_phrase(holiday):
    return {
        "설날": "설 연휴에도 시민의 발을 책임져 주셔서 감사합니다.",
        "추석": "추석 연휴에도 안전한 운행을 부탁드립니다.",
        "주말": "주말에도 평소처럼 안전운전을 부탁드립니다.",
    }.get(holiday, "")

# 메시지 생성 함수 (GPT 활용)
def generate_gpt_message(base_msg, tags, tone, msg_type, weather, holiday):
    tag_text = ", ".join(tags)
    weather_phrase = get_weather_phrase(weather)
    holiday_phrase = get_holiday_phrase(holiday)

    prompt = (
        f"다음은 '{msg_type}' 대상 운전기사에게 보내는 공지 메시지입니다. 메시지를 '{tone}' 톤으로 반드시 '존댓말'로 다시 써주세요.\n"
        f"다음 태그를 강조해주세요: {tag_text}.\n"
        f"메시지는 '{weather}' 날씨이며 '{holiday}'입니다. 다음 문장을 자연스럽게 반영해주세요:\n"
        f"- 날씨 문구: {weather_phrase}\n"
        f"- 날짜 문구: {holiday_phrase}\n"
        f"\n[기존 메시지]\n{base_msg}\n"
        f"\n[변환된 메시지]"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GPT 호출 실패: {e}"

# 추천 버튼
if st.button("🔍 메시지 추천받기"):
    # 태그 + 유형 필터링
    def has_tag(tag_list):
        try:
            tags = eval(tag_list)
            return any(tag in tags for tag in selected_tags)
        except:
            return False

    filtered = df[
        df["태그"].apply(has_tag) &
        df["유형"].fillna("") == selected_type
    ]



    # fallback: 태그만 일치하는 메시지로 대체 추천
    if filtered.empty:
        fallback = df[df["태그"].apply(has_tag)]
        if not fallback.empty:
            base_msg = fallback.sample(1).iloc[0]["메시지"]
            gpt_msg = generate_gpt_message(base_msg, selected_tags, selected_tone, selected_type, selected_weather, selected_holiday)

            st.info("📌 조건과 정확히 일치하지는 않지만, 유사한 메시지를 추천드립니다:")
            st.success(gpt_msg)
        else:
            st.warning("조건에 맞는 메시지가 없습니다. 태그와 유형을 다시 선택해주세요.")
    else:
        base_msg = filtered.sample(1).iloc[0]["메시지"]
        gpt_msg = generate_gpt_message(base_msg, selected_tags, selected_tone, selected_type, selected_weather, selected_holiday)

        st.info("📝 기존 메시지:")
        st.write(base_msg)

        st.success("✨ 변형된 추천 메시지:")
        st.write(gpt_msg)