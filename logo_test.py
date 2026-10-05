import os
import base64
import requests

from dotenv import load_dotenv


# =============================
# API KEY
# =============================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY가 없습니다.")
    exit()


# =============================
# 이미지 모델
# =============================

model = "gemini-3.1-flash-lite-image"

url = (
    f"https://generativelanguage.googleapis.com/v1/"
    f"models/{model}:generateContent"
)


# =============================
# 로고 프롬프트
# =============================

prompt = """
Create a simple professional logo for an AI creative education brand.

Brand name: CreAI

Target:
Elementary school children and parents.

Concept:
Children turn imagination into digital creations using AI.

Style:
minimal,
warm,
creative,
future-oriented,
simple geometric symbol,
flat vector style,
clean white background,
no photograph,
no mockup,
no 3D.

Create only one simple logo.
"""


# =============================
# 요청 데이터
# =============================

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ],
    "generationConfig": {
        "responseModalities": [
            "IMAGE"
        ]
    }
}


headers = {
    "x-goog-api-key": api_key,
    "Content-Type": "application/json"
}


print("🎨 Gemini 로고 생성 시작")
print("모델:", model)
print("최대 대기시간: 60초")
print()


# =============================
# API 호출
# =============================

try:

    response = requests.post(
        url,
        headers=headers,
        json=payload,

        # 연결 10초 / 응답 최대 60초
        timeout=(10, 60)
    )

    print("HTTP 상태 코드:", response.status_code)

    if response.status_code != 200:

        print("❌ API 호출 실패")
        print(response.text)
        exit()


    result = response.json()


    # =============================
    # 이미지 데이터 검색
    # =============================

    image_found = False

    candidates = result.get(
        "candidates",
        []
    )

    for candidate in candidates:

        parts = (
            candidate
            .get("content", {})
            .get("parts", [])
        )

        for part in parts:

            inline_data = (
                part.get("inlineData")
                or
                part.get("inline_data")
            )

            if inline_data:

                image_data = inline_data.get(
                    "data"
                )

                if image_data:

                    os.makedirs(
                        "output",
                        exist_ok=True
                    )

                    image_bytes = (
                        base64.b64decode(
                            image_data
                        )
                    )

                    file_path = (
                        "output/logo_test.png"
                    )

                    with open(
                        file_path,
                        "wb"
                    ) as file:

                        file.write(
                            image_bytes
                        )

                    print(
                        "✅ 로고 이미지 저장 성공!"
                    )

                    print(
                        "📁",
                        file_path
                    )

                    image_found = True
                    break

        if image_found:
            break


    if not image_found:

        print(
            "❌ 응답은 받았지만 "
            "이미지를 찾지 못했습니다."
        )

        print(result)


except requests.exceptions.ReadTimeout:

    print()
    print(
        "⏰ 60초 동안 응답이 없어 "
        "요청을 중단했습니다."
    )


except requests.exceptions.ConnectTimeout:

    print()
    print(
        "❌ Gemini 서버 연결 시간이 "
        "초과되었습니다."
    )


except Exception as e:

    print()
    print(
        "❌ 이미지 생성 중 오류 발생"
    )

    print(type(e).__name__)
    print(e)