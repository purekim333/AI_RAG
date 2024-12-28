import os
import requests
import xml.etree.ElementTree as ET

# API 기본 정보
url = 'https://www.youthcenter.go.kr/opi/youthPlcyList.do'  # 실제 API URL로 변경
API_KEY = ''  # 발급받은 인증키

# 파라미터 기본값
params = {
    "openApiVlak": API_KEY,
    "display": 100,  # 최대 100건 요청
    "pageIndex": 1,
}

category_names = {
    "023010": "일자리",
    "023020": "주거",
    "023030": "교육",
    "023040": "복지문화",
    "023050": "참여권리"
}

# 데이터 저장 루트 폴더
root_folder = "policies"
os.makedirs(root_folder, exist_ok=True)

# 데이터 수집 및 저장
while True:
    # API 호출
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        break

    # XML 파싱
    root = ET.fromstring(response.text)
    policies = root.findall("youthPolicy")
    
    if not policies:
        print("No more data available.")
        break

    for policy in policies:
        # 정책 데이터 추출
        polyRlmCd = policy.find("polyRlmCd").text  # 정책분야코드
        bizId = policy.find("bizId").text          # 정책 ID
        title = policy.find("polyBizSjnm").text    # 정책명
        description = policy.find("polyItcnCn").text  # 정책 소개
        details = policy.find("sporCn").text      # 세부 정보
        age_info = policy.find("ageInfo").text    # 대상 연령
        apply_period = policy.find("rqutPrdCn").text  # 신청 기간
        apply_procedure = policy.find("rqutProcCn").text  # 신청 절차
        contact = policy.find("cherCtpcCn").text # 담당자 연락처 

        # 폴더 생성 (정책분야코드별)
        category_folder = os.path.join(root_folder, category_names[polyRlmCd])
        os.makedirs(category_folder, exist_ok=True)

        # 파일 이름 및 경로 설정
        file_name = f"{bizId}.txt"
        file_path = os.path.join(category_folder, file_name)

        # 파일 내용 작성
        file_content = (
            f"정책 ID: {bizId}\n"
            f"정책명: {title}\n"
            f"내용: {description}\n"
            f"세부 정보: {details}\n"
            f"대상 연령: {age_info}\n"
            f"신청 기간: {apply_period}\n"
            f"신청 절차: {apply_procedure}\n"
            f"담당자 연락처: {contact}"
        )

        # 파일 저장
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(file_content)

    # 다음 페이지로 이동
    params["pageIndex"] += 1

print("모든 정책 데이터가 저장되었습니다.")
