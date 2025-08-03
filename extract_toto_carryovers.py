import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# GitHub Issue 생성 함수
def create_github_issue(token, repo, title, body):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("✅ GitHub 이슈가 성공적으로 생성되었습니다.")
    else:
        print(f"❌ GitHub 이슈 생성 실패: {response.status_code} - {response.text}")

# HTML 파싱 예시 (간단히 구조화된 예)
def parse_carryover_info():
    # 여기서는 테스트용 하드코딩 데이터 사용
    tables = [
        ["第1556回", "1等", "2等", "3等"],
        ["当せん金", "0円", "447,240円", "78,570円"],
        ["当せん口数", "0口", "13口", "74口"],
        ["次回への繰越金", "27,133,015円", "0円", "0円"]
    ]

    # 텍스트 정렬
    col_widths = [max(len(row[i]) for row in tables) for i in range(len(tables[0]))]

    lines = []
    for row in tables:
        line = " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
        lines.append(line)

    formatted_table = "\n".join(lines)
    return "第1556回 toto 2713万円 移越発生", formatted_table

if __name__ == "__main__":
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")

    title, body = parse_carryover_info()

    print("[🔍 이슈 제목 예시]")
    print(title)
    print("\n[🔍 이슈 본문 예시]\n")
    print(body)

    if GITHUB_TOKEN and GITHUB_REPOSITORY:
        create_github_issue(GITHUB_TOKEN, GITHUB_REPOSITORY, title, body)
    else:
        print("⚠️ GitHub 토큰 또는 저장소 정보가 없습니다. 이슈를 생성하지 않습니다.")
