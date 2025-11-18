from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
import time
import logging
import uuid
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
# CORS 설정 - 개발 환경에서는 모든 origin 허용
# 프로덕션에서는 특정 도메인만 허용하도록 변경하세요
CORS(app, resources={r"/*": {"origins": "*"}})

COMFY_API_URL = os.getenv("COMFY_API_URL", "http://192.168.1.50:8188").rstrip('/')
WORKFLOW_DIR = os.getenv("WORKFLOW_DIR", "workflows")
OUTPUT_DIR = os.getenv("COMFY_OUTPUT_DIR", "{COMFY_API_URL}/output")

logging.basicConfig(level=logging.DEBUG)

# OpenAI 클라이언트 초기화
openai_client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        logging.info("OpenAI client initialized successfully")
    else:
        logging.warning("OPENAI_API_KEY not found in environment variables")
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client: {e}")


def load_workflow(workflow_name):
    try:
        with open(os.path.join(WORKFLOW_DIR, workflow_name), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"워크플로우를 로드할 수 없습니다: {str(e)}"}


def set_unique_filename(workflow, unique_id, index=None, item_id=None, subfolder=None):
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") == "SaveImage":
            # 기본 파일 이름 생성
            if item_id is not None and index is not None:
                filename = f"background_id={item_id}_{index:02d}_{unique_id}"
            elif index is not None:
                filename = f"background_{index:02d}_{unique_id}"
            else:
                filename = f"background_{unique_id}"
            
            # subfolder를 포함한 파일 경로 생성
            if subfolder:
                filename_prefix = f"{subfolder}/{filename}"
            else:
                filename_prefix = filename
            
            if "inputs" in node:
                node["inputs"]["filename_prefix"] = filename_prefix
                # subfolder key는 삭제 (filename_prefix에 포함됐기 때문)
                node["inputs"].pop("subfolder", None)
    
    return workflow


def generate_single(prompt, workflow_name, subfolder):
    workflow = load_workflow(workflow_name)
    if "error" in workflow:
        return jsonify(workflow), 500
    
    # 프롬프트를 워크플로우 내에 반영
    for node in workflow.values():
        if (
            isinstance(node, dict)
            and node.get("class_type") == "CLIPTextEncode"
            and node.get("_meta", {}).get("title") == "Positive Prompt"
        ):
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = prompt
    
    workflow = set_unique_filename(workflow, str(uuid.uuid4())[:8], subfolder=subfolder)
    
    for node in workflow.values():
        if node.get("class_type") in ["KSampler", "KSamplerAdvanced", "Seed"]:
            if "inputs" in node and "seed" in node["inputs"]:
                node["inputs"]["seed"] = int(time.time())
    
    try:
        res = requests.post(f"{COMFY_API_URL}/prompt", json={"prompt": workflow})
        res.raise_for_status()
        prompt_id = res.json().get("prompt_id")
        
        image_url = wait_for_image(prompt_id, subfolder)
        logging.info(f"Generated image URL: {image_url}")
        
        return jsonify({"image_url": image_url})
    except Exception as e:
        logging.error(f"Error in generate_single: {e}")
        return jsonify({"error": str(e)}), 500


def generate_backgrounds(background_items, workflow_name, subfolder):
    results = []
    batch_id = str(uuid.uuid4())[:8]
    original_workflow = load_workflow(workflow_name)
    
    # ❗1. 워크플로우가 에러인지 먼저 확인
    if not isinstance(original_workflow, dict) or "error" in original_workflow:
        return jsonify(original_workflow), 500
    
    for idx, item in enumerate(background_items):
        # ❗2. 아이템이 dict가 아니면 continue
        if not isinstance(item, dict):
            results.append("invalid")
            continue
        
        # deepcopy
        workflow = json.loads(json.dumps(original_workflow))
        
        item_id = item.get("id", None)
        prompt = item.get("background") or item.get("background_image", "")
        prompt = prompt.strip()
        
        # ❗3. 프롬프트가 없으면 스킵
        if not prompt:
            results.append("empty")
            continue
        
        for node in workflow.values():
            if (
                isinstance(node, dict)
                and node.get("class_type") == "CLIPTextEncode"
                and node.get("_meta", {}).get("title") == "Positive Prompt"
            ):
                if "inputs" in node and "text" in node["inputs"]:
                    node["inputs"]["text"] = prompt
        
        # ❗4. 워크플로우에 고유 파일명 설정
        workflow = set_unique_filename(workflow, batch_id, idx, item_id, subfolder=subfolder)
        
        # ❗5. workflow가 dict가 아닐 경우 대비
        if not isinstance(workflow, dict):
            results.append("error")
            continue
        
        # Seed 설정
        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") in ["KSampler", "KSamplerAdvanced", "Seed"]:
                if "inputs" in node and "seed" in node["inputs"]:
                    node["inputs"]["seed"] = int(time.time()) + (idx + 1) * 10000
        
        try:
            # 프롬프트 전송
            res = requests.post(f"{COMFY_API_URL}/prompt", json={"prompt": workflow})
            res.raise_for_status()
            prompt_id = res.json().get("prompt_id")
            
            # 이미지 대기
            result = wait_for_image(prompt_id, subfolder, idx)
            results.append(result)
        except Exception as e:
            results.append(f"error: {str(e)}")
        
        time.sleep(2)
    
    return jsonify({"image_urls": results})


def wait_for_image(prompt_id, subfolder, idx=None):
    """ComfyUI에서 이미지가 생성될 때까지 대기하고 Flask 프록시 URL 반환"""
    while True:
        time.sleep(0.5)
        try:
            history = requests.get(f"{COMFY_API_URL}/history/{prompt_id}").json()
            if prompt_id in history:
                for output in history[prompt_id].get("outputs", {}).values():
                    if "images" in output and output["images"]:
                        image = output["images"][0]
                        filename = image["filename"]
                        image_type = image.get("type", "output")
                        folder = subfolder if subfolder else image.get("subfolder", "")
                        
                        # Flask 프록시 URL 생성 (CORS 문제 해결)
                        url = f"http://127.0.0.1:5000/api/image?filename={filename}&type={image_type}"
                        if folder:
                            url += f"&subfolder={folder}"
                        
                        # 캐시 방지용 타임스탬프 추가
                        url += f"&cb={int(time.time())}"
                        
                        return url
        except Exception as e:
            logging.debug(f"Waiting for image generation: {e}")
            continue


@app.route("/workflows", methods=["GET"])
def list_workflows():
    try:
        files = os.listdir(WORKFLOW_DIR)
        json_files = [f for f in files if f.endswith(".json")]
        return jsonify({"workflows": json_files})
    except Exception as e:
        return jsonify({"error": "워크플로우 목록을 불러올 수 없습니다.", "detail": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    workflow_name = data.get("workflow")
    subfolder = data.get("subfolder")
    prompt_data = data.get("prompt")
    
    try:
        # 1. 단일 문자열 프롬프트
        if isinstance(prompt_data, str):
            result = generate_single(prompt_data, workflow_name, subfolder)
            # generate_single은 이미 jsonify된 Response 객체를 반환
            return result
        elif isinstance(prompt_data, dict) and "events" in prompt_data:
            result = generate_backgrounds(prompt_data["events"], workflow_name, subfolder)
            # generate_backgrounds도 이미 jsonify된 Response 객체를 반환
            return result
        else:
            return jsonify({"error": "지원하지 않는 형식입니다. 'prompt' 또는 'events' 키를 사용하세요."}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "서버 내부 오류", "detail": str(e)}), 500


@app.route("/api/image", methods=["GET"])
def proxy_image():
    """ComfyUI 이미지를 프록시하여 CORS 문제 해결"""
    try:
        filename = request.args.get("filename")
        image_type = request.args.get("type", "output")
        subfolder = request.args.get("subfolder", "")
        
        if not filename:
            return jsonify({"error": "filename parameter is required"}), 400
        
        # ComfyUI API로 이미지 요청
        params = {
            "filename": filename,
            "type": image_type
        }
        if subfolder:
            params["subfolder"] = subfolder
        
        response = requests.get(f"{COMFY_API_URL}/api/view", params=params, stream=True)
        response.raise_for_status()
        
        # 이미지를 그대로 전달 (CORS 헤더 포함)
        from flask import Response
        return Response(
            response.content,
            mimetype=response.headers.get('content-type', 'image/png'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        logging.error(f"Error proxying image: {e}")
        return jsonify({"error": "Failed to fetch image", "detail": str(e)}), 500


@app.route("/output/<path:filename>")
def serve_image(filename):
    try:
        return send_from_directory(OUTPUT_DIR, filename)
    except Exception as e:
        return jsonify({"error": "이미지를 서빙할 수 없습니다.", "detail": str(e)}), 404


@app.route("/output/latest")
def serve_latest_image():
    files = [f for f in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, f))]
    if not files:
        return jsonify({"error": "이미지가 없습니다."}), 404
    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)))
    return send_from_directory(OUTPUT_DIR, latest)


@app.route("/generate-event", methods=["POST"])
def generate_event():
    """OpenAI를 사용하여 게임 이벤트 생성"""
    if not openai_client:
        return jsonify({"error": "OpenAI client is not initialized. Please check your API key."}), 503
    
    try:
        data = request.json
        category = data.get("category", "forest exploration")
        
        # OpenAI Function Calling 정의
        tools = [{
            "type": "function",
            "function": {
                "name": "generate_event",
                "description": "Generate a roguelike game event with associated tags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "string",
                            "description": "string of tags related to the event in english. The first string MUST always be **'forest'**."
                        },
                        "background_image": {
                            "type": "string",
                            "description": "Detailed background description of the event scene for visualization in english"
                        }
                    },
                    "required": ["tags", "background_image"]
                }
            }
        }]
        
        # 시스템 프롬프트
        system_prompt = """너는 굉장히 뛰어난 게임 시나리오 창작가야.
user가 제시한 주제에 대해 로그라이크 게임 이벤트와 관련 태그를 만들어줘.
게임 테마는 "forest"야.

1. background_image:
- 이벤트 내에서 모험가가 마주하게 될 장면을 시각적으로 상세히 묘사하세요.
- flux schnell 모델이 이미지를 생성할 수 있도록 영문 프롬프트로 만들어줘.

2. tags:
- 이벤트의 테마, 주제, 요소, 잠재적 게임플레이 영향을 분류하는 약 5개의 관련 tags를 영어로 생성하세요.
- tags에는 반드시 background_image에서 묘사된 주요 시각적 요소와 분위기를 반영하는 단어들이 포함되어야 합니다.
- tags에는 처음에 반드시, 테마인 "forest"가 들어가야합니다.

예시:
{
  "tags": "forest, wounded warrior, bandage, healing, nature",
  "background_image": "Dim sunlight shines through ancient trees, and beneath them, a wounded warrior lies resting against tree bark. His face is contorted with pain, and the fallen branches and blood-soaked ground around him tell the story of combat. On the ground are his broken sword and a few scattered medicinal herbs."
}"""
        
        # OpenAI API 호출
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'"{category}"를 주제로하는 로그라이크 게임 이벤트를 생성해주세요.'}
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "generate_event"}},
            temperature=0.8
        )
        
        # 응답 파싱
        message = completion.choices[0].message
        if message.tool_calls and message.tool_calls[0].function.name == "generate_event":
            event_data = json.loads(message.tool_calls[0].function.arguments)
            return jsonify(event_data)
        else:
            return jsonify({"error": "Function call not received from OpenAI"}), 500
    
    except Exception as e:
        logging.error(f"Error generating event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to generate event", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)