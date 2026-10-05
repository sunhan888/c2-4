import os
import json
import time
import base64

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import font_manager, rc


# =========================================================
# 0. 한글 폰트 설정
# =========================================================

def set_korean_font():
    try:
        font_path = "C:/Windows/Fonts/malgun.ttf"

        if os.path.exists(font_path):
            font_name = font_manager.FontProperties(
                fname=font_path
            ).get_name()

            rc("font", family=font_name)
            plt.rcParams["axes.unicode_minus"] = False

    except Exception:
        pass


set_korean_font()


# =========================================================
# 1. 환경 변수 불러오기
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY를 찾을 수 없습니다.")
    print(".env 파일을 확인해주세요.")
    exit()


if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY를 찾을 수 없습니다.")
    print(".env 파일을 확인해주세요.")
    exit()


# =========================================================
# 2. API 클라이언트 생성
# =========================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=90.0
)


# =========================================================
# 3. Gemini 텍스트 모델 목록
# =========================================================

# 실제 이전 실행에서 성공했던 모델을 가장 먼저 사용
TEXT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-latest"
]


# =========================================================
# 4. 브랜드 브리프 읽기
# =========================================================

def load_brief(file_path):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            brief = json.load(file)


    except FileNotFoundError:

        print(
            f"❌ 파일을 찾을 수 없습니다: "
            f"{file_path}"
        )

        return None


    except json.JSONDecodeError:

        print(
            "❌ JSON 파일 형식이 "
            "올바르지 않습니다."
        )

        return None


    except Exception as e:

        print(
            "❌ 브리프 파일을 읽는 중 "
            "오류가 발생했습니다."
        )

        print(e)

        return None


    # 필수 필드
    required_fields = [
        "industry",
        "target",
        "keywords"
    ]


    missing_fields = []

    for field in required_fields:

        if field not in brief:
            missing_fields.append(field)


    if missing_fields:

        print(
            "❌ 필수 입력 항목이 없습니다."
        )

        print(
            "누락 항목:",
            ", ".join(missing_fields)
        )

        return None


    return brief


# =========================================================
# 5. Gemini 응답 JSON 변환
# =========================================================

def parse_json_response(text):

    if not text:
        return None


    cleaned = text.strip()


    # markdown 코드 블록 제거
    if cleaned.startswith("```"):

        cleaned = cleaned.replace(
            "```json",
            ""
        )

        cleaned = cleaned.replace(
            "```JSON",
            ""
        )

        cleaned = cleaned.replace(
            "```",
            ""
        )

        cleaned = cleaned.strip()


    # 바로 JSON 변환
    try:

        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass


    # 응답 안에 JSON만 추출
    try:

        start = cleaned.find("{")
        end = cleaned.rfind("}")


        if start != -1 and end != -1:

            json_text = cleaned[
                start:end + 1
            ]

            return json.loads(
                json_text
            )


    except Exception:
        pass


    return None


# =========================================================
# 6. Gemini 텍스트 API 호출
# =========================================================

def call_gemini_text(prompt):

    for model_name in TEXT_MODELS:

        print(
            f"  → 모델 시도: "
            f"{model_name}"
        )


        for attempt in range(3):

            try:

                interaction = (
                    gemini_client
                    .interactions
                    .create(
                        model=model_name,
                        input=prompt,

                        generation_config={
                            "temperature": 0.8
                        },

                        # 핵심 수정
                        # 요청 최대 30초
                        timeout=30
                    )
                )


                text = interaction.output_text


                if text:

                    print(
                        f"  ✅ 성공: "
                        f"{model_name}"
                    )

                    return text


            except Exception as e:

                print(
                    f"  ⚠️ 호출 실패 "
                    f"({attempt + 1}/3)"
                )

                print(
                    f"     {type(e).__name__}"
                )


                if attempt < 2:

                    wait_time = (
                        2 ** attempt
                    )

                    print(
                        f"  → {wait_time}초 후 "
                        "재시도합니다."
                    )

                    time.sleep(
                        wait_time
                    )


                else:

                    print(
                        f"  → {model_name} 실패, "
                        "다음 모델로 전환합니다."
                    )


    print(
        "❌ 모든 Gemini 텍스트 "
        "모델 호출에 실패했습니다."
    )

    return None


# =========================================================
# 7. 브랜드 아이덴티티 생성
# =========================================================

def generate_brand_identity(brief):

    competitors = brief.get(
        "competitors",
        []
    )

    tone = brief.get(
        "tone",
        "전문적이고 신뢰감 있는"
    )

    notes = brief.get(
        "notes",
        "없음"
    )


    prompt = f"""
당신은 전문 브랜드 전략가이자
브랜드 네이밍 디렉터입니다.

아래 브랜드 브리프를 분석해서
브랜드 아이덴티티를 설계해주세요.


[브랜드 브리프]


업종:
{brief["industry"]}


타겟:
{brief["target"]}


키워드:
{", ".join(brief["keywords"])}


톤앤매너:
{tone}


경쟁사:
{", ".join(competitors) if competitors else "없음"}


추가 요청사항:
{notes}



다음 정보를 모두 생성하세요.


1. 브랜드 네이밍 후보 정확히 5개

각 후보는 다음 정보를 포함합니다.

- name
- english_name
- meaning


2. 슬로건 정확히 3개


3. 브랜드 스토리

약 300자 내외로 작성하며

- 브랜드 탄생 배경
- 브랜드 철학
- 브랜드 비전

을 포함합니다.


4. 컬러 팔레트

메인 컬러 1개

서브 컬러 3개

모든 색상은 반드시
#RRGGBB 형식의 HEX 코드로 작성합니다.

각 색상에는

- hex
- name
- meaning

을 포함합니다.


5. 경쟁사가 있다면
차별화 포인트 3개를 작성합니다.


반드시 아래 JSON 구조만 출력하세요.

Markdown 코드블록이나
추가 설명은 출력하지 마세요.


{{
    "names": [
        {{
            "name": "브랜드명",
            "english_name": "English Name",
            "meaning": "의미와 네이밍 의도"
        }}
    ],

    "slogans": [
        "슬로건 1",
        "슬로건 2",
        "슬로건 3"
    ],

    "story": "브랜드 스토리",

    "colors": {{
        "main": {{
            "hex": "#000000",
            "name": "Color Name",
            "meaning": "색상 의미"
        }},

        "sub": [
            {{
                "hex": "#000000",
                "name": "Color Name",
                "meaning": "색상 의미"
            }}
        ]
    }},

    "differentiation": [
        "차별화 포인트 1",
        "차별화 포인트 2",
        "차별화 포인트 3"
    ]
}}
"""


    result_text = call_gemini_text(
        prompt
    )


    if not result_text:

        return None


    result = parse_json_response(
        result_text
    )


    if result is None:

        print(
            "⚠️ Gemini 응답을 "
            "JSON으로 변환하지 못했습니다."
        )

        return {
            "raw_response": result_text
        }


    return result


# =========================================================
# 8. 컬러 팔레트 PNG 생성
# =========================================================

def create_color_palette(
    brand_result,
    output_dir
):

    try:

        colors = brand_result.get(
            "colors"
        )


        if not colors:

            print(
                "⚠️ 컬러 데이터가 없어 "
                "팔레트를 만들 수 없습니다."
            )

            return None


        palette = []


        main_color = colors.get(
            "main"
        )


        if main_color:

            palette.append(
                main_color
            )


        sub_colors = colors.get(
            "sub",
            []
        )


        for color in sub_colors:

            palette.append(
                color
            )


        if not palette:

            print(
                "⚠️ 사용할 컬러가 없습니다."
            )

            return None


        fig, ax = plt.subplots(
            figsize=(10, 3)
        )


        ax.set_xlim(
            0,
            len(palette)
        )


        ax.set_ylim(
            0,
            1
        )


        ax.axis(
            "off"
        )


        for i, color in enumerate(
            palette
        ):

            hex_code = color.get(
                "hex",
                "#CCCCCC"
            )


            color_name = color.get(
                "name",
                "Color"
            )


            rectangle = Rectangle(
                (i, 0.25),
                1,
                0.75,
                facecolor=hex_code
            )


            ax.add_patch(
                rectangle
            )


            ax.text(
                i + 0.5,
                0.15,
                f"{color_name}\n{hex_code}",
                ha="center",
                va="center",
                fontsize=10
            )


        file_path = os.path.join(
            output_dir,
            "color_palette.png"
        )


        plt.savefig(
            file_path,
            dpi=200,
            bbox_inches="tight"
        )


        plt.close()


        print(
            f"  ✅ 컬러 팔레트 저장: "
            f"{file_path}"
        )


        return file_path


    except Exception as e:

        print(
            "⚠️ 컬러 팔레트 생성 중 "
            "오류가 발생했습니다."
        )

        print(e)

        return None


# =========================================================
# 9. OpenAI 로고 이미지 생성
# =========================================================

def generate_logo(
    brand_result,
    brief,
    output_dir,
    logo_number
):

    brand_name = "New Brand"


    names = brand_result.get(
        "names",
        []
    )


    if names:

        brand_name = names[0].get(
            "name",
            "New Brand"
        )


    tone = brief.get(
        "tone",
        "modern and professional"
    )


    keywords = ", ".join(
        brief.get(
            "keywords",
            []
        )
    )


    colors = brand_result.get(
        "colors",
        {}
    )


    main_color = (
        colors
        .get("main", {})
        .get("hex", "#333333")
    )


    sub_colors = colors.get(
        "sub",
        []
    )


    sub_hex = [
        color.get(
            "hex",
            ""
        )
        for color
        in sub_colors
    ]


    # 로고마다 디자인 방향을 다르게
    styles = [

        """
minimal modern vector logo,
simple geometric symbol,
clean and memorable,
professional technology education brand
""",

        """
warm creative vector logo,
friendly abstract symbol,
soft organic shapes,
playful but professional education brand
""",

        """
future-oriented premium vector logo,
modern symbolic mark,
clean professional identity
"""
    ]


    style = styles[
        (logo_number - 1)
        % len(styles)
    ]


    prompt = f"""
Create a professional brand logo.

Brand name:
{brand_name}

Industry:
{brief["industry"]}

Target audience:
{brief["target"]}

Brand keywords:
{keywords}

Brand tone:
{tone}

Main brand color:
{main_color}

Supporting colors:
{", ".join(sub_hex)}


Logo concept:
{style}


Design requirements:

- create only the finished logo
- square 1:1 composition
- clean white background
- flat vector-style design
- simple recognizable symbol
- professional brand identity
- suitable for website, app and print
- visually appropriate for children and parents
- use the provided brand colors
- include the brand name clearly
- centered composition
- no business card mockup
- no packaging mockup
- no merchandise
- no photograph
- no 3D render
- no realistic scene
"""


    print(
        "  → OpenAI 이미지 API로 "
        "로고 생성 중..."
    )


    for attempt in range(2):

        try:

            result = (
                openai_client
                .images
                .generate(
                    model=(
                        "gpt-image-2.5-flare"
                    ),

                    prompt=prompt,

                    n=1,

                    size="1024x1024",

                    quality="low",

                    output_format="png"
                )
            )


            image_base64 = (
                result
                .data[0]
                .b64_json
            )


            if not image_base64:

                raise ValueError(
                    "이미지 데이터가 "
                    "반환되지 않았습니다."
                )


            image_bytes = (
                base64.b64decode(
                    image_base64
                )
            )


            file_path = os.path.join(
                output_dir,
                f"logo_{logo_number:02d}.png"
            )


            with open(
                file_path,
                "wb"
            ) as file:

                file.write(
                    image_bytes
                )


            print(
                f"  ✅ 로고 저장: "
                f"{file_path}"
            )


            return file_path


        except Exception as e:

            print(
                f"  ⚠️ 로고 생성 실패 "
                f"({attempt + 1}/2)"
            )

            print(
                f"     {type(e).__name__}: "
                f"{e}"
            )


            if attempt == 0:

                print(
                    "  → 3초 후 "
                    "다시 시도합니다."
                )

                time.sleep(3)


            else:

                print(
                    f"❌ 로고 {logo_number} "
                    "생성에 실패했습니다."
                )

                return None


# =========================================================
# 10. JSON 결과 저장
# =========================================================

def save_result(
    brand_result,
    brief,
    output_dir
):

    result_data = {

        "brief": brief,

        "brand_identity":
            brand_result
    }


    file_path = os.path.join(
        output_dir,
        "brand_result.json"
    )


    try:

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result_data,
                file,
                ensure_ascii=False,
                indent=4
            )


        print(
            f"  ✅ 결과 저장: "
            f"{file_path}"
        )


        return file_path


    except Exception as e:

        print(
            "❌ JSON 저장 중 "
            "오류가 발생했습니다."
        )

        print(e)

        return None


# =========================================================
# 11. 브랜드 결과 터미널 출력
# =========================================================

def print_brand_result(
    result
):

    print()

    print(
        "=" * 60
    )

    print(
        "✨ AI 브랜드 아이덴티티 결과"
    )

    print(
        "=" * 60
    )


    # 네이밍
    names = result.get(
        "names",
        []
    )


    if names:

        print()

        print(
            "🏷️ 브랜드 네이밍"
        )


        for index, item in enumerate(
            names,
            start=1
        ):

            print(
                f"{index}. "
                f"{item.get('name', '')} "
                f"({item.get('english_name', '')})"
            )


            print(
                f"   "
                f"{item.get('meaning', '')}"
            )


    # 슬로건
    slogans = result.get(
        "slogans",
        []
    )


    if slogans:

        print()

        print(
            "💬 슬로건"
        )


        for slogan in slogans:

            print(
                f"- {slogan}"
            )


    # 스토리
    story = result.get(
        "story"
    )


    if story:

        print()

        print(
            "📖 브랜드 스토리"
        )

        print(
            story
        )


    # 컬러
    colors = result.get(
        "colors"
    )


    if colors:

        print()

        print(
            "🎨 컬러"
        )


        main = colors.get(
            "main",
            {}
        )


        print(
            "메인:",
            main.get("hex", ""),
            main.get("name", "")
        )


        for item in colors.get(
            "sub",
            []
        ):

            print(
                "서브:",
                item.get("hex", ""),
                item.get("name", "")
            )


    # 경쟁사 분석
    differentiation = result.get(
        "differentiation",
        []
    )


    if differentiation:

        print()

        print(
            "🚀 경쟁사 차별화 포인트"
        )


        for item in differentiation:

            print(
                f"- {item}"
            )


# =========================================================
# 12. 메인 프로그램
# =========================================================

def main():

    print()

    print(
        "🎨 AI 브랜드 아이덴티티 생성기"
    )

    print(
        "=" * 45
    )

    print()


    # -----------------------------
    # 브리프 파일
    # -----------------------------

    brief_path = input(
        "브리프 파일 경로를 입력하세요: "
    ).strip()


    if not brief_path:

        print(
            "❌ 브리프 파일 경로는 "
            "필수입니다."
        )

        return


    # -----------------------------
    # 출력 폴더
    # -----------------------------

    output_dir = input(
        "출력 폴더 경로를 입력하세요 "
        "(엔터 시 ./output): "
    ).strip()


    if not output_dir:

        output_dir = "./output"


    os.makedirs(
        output_dir,
        exist_ok=True
    )


    # -----------------------------
    # 브리프 로딩
    # -----------------------------

    brief = load_brief(
        brief_path
    )


    if not brief:

        return


    print()

    print(
        "✅ 브랜드 브리프를 "
        "정상적으로 불러왔습니다."
    )


    print(
        f"업종: "
        f"{brief['industry']}"
    )


    print(
        f"타겟: "
        f"{brief['target']}"
    )


    print(
        "키워드:",
        ", ".join(
            brief["keywords"]
        )
    )


    # =====================================================
    # 1 / 5
    # =====================================================

    print()

    print(
        "[1/5] 브랜드 네이밍, "
        "슬로건, 스토리 생성 중..."
    )


    brand_result = (
        generate_brand_identity(
            brief
        )
    )


    if not brand_result:

        print()

        print(
            "❌ 브랜드 텍스트 생성에 "
            "실패했습니다."
        )

        return


    print_brand_result(
        brand_result
    )


    # =====================================================
    # 2 / 5
    # =====================================================

    print()

    print(
        "[2/5] 컬러 팔레트 "
        "시각화 중..."
    )


    create_color_palette(
        brand_result,
        output_dir
    )


    # =====================================================
    # 3 / 5
    # =====================================================

    print()

    print(
        "[3/5] 브랜드 결과 "
        "저장 중..."
    )


    save_result(
        brand_result,
        brief,
        output_dir
    )


    # =====================================================
    # 4 / 5
    # =====================================================

    print()

    print(
        "[4/5] 로고 시안 1 "
        "생성 중..."
    )


    generate_logo(
        brand_result,
        brief,
        output_dir,
        1
    )


    # =====================================================
    # 5 / 5
    # =====================================================

    print()

    print(
        "[5/5] 로고 시안 2 "
        "생성 중..."
    )


    generate_logo(
        brand_result,
        brief,
        output_dir,
        2
    )


    # =====================================================
    # 완료
    # =====================================================

    print()

    print(
        "=" * 60
    )

    print(
        "✅ 브랜드 생성 작업 완료!"
    )

    print(
        "=" * 60
    )


    print()

    print(
        f"📁 결과 폴더: "
        f"{output_dir}"
    )


    print()

    print(
        "생성 결과:"
    )

    print(
        "- brand_result.json"
    )

    print(
        "- color_palette.png"
    )

    print(
        "- logo_01.png"
    )

    print(
        "- logo_02.png"
    )

    print()


# =========================================================
# 프로그램 실행
# =========================================================

if __name__ == "__main__":

    main()