import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
from github import Github

# 🎯 타겟 날짜 (테스트용으로 고정, 실제 자동화 시에는 datetime.today().strftime('%Y.%m.%d') 사용)
TARGET_DATE = "2025.08.02"

# 🎯 이월금 테이블 인식 키워드
CARRYOVER_KEY = "次回への繰越金"

# 🎯 GitHub 설정
REPO_NAME = "사용자명/레포명"  # 실제 사용자 레포로 바꿔주세요
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_html():
    url = "https://www.toto-dream.com/toto/result/"
    res = requests.get(url)
    res.encoding = "utf-8"
    return BeautifulSoup(res.text, "html.parser")

def extract_sections(soup):
    return soup.select("div.section")

def extract_tables(soup):
    return soup.select("table.typeTK")

def is_date_in_text(date, text):
    return date in text.replace("/", ".")

def transpose_table(table):
    rows = table.find_all("tr")
    grid = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        grid.append([cell.get_text(strip=True) for cell in cells])
    return list(map(list, zip(*grid)))

def format_markdown_table(transposed):
    headers = transposed[0]
    rows = transposed[1:]

    # |:---| 스타일과 함께 헤더 렌더링
    md = "|               | " + " | ".join(headers[1:]) + " |\n"
    md += "|:--------------| " + " | ".join([":" + "-" * max(len(col), 4) for col in headers[1:]]) + " |\n"

    for row in rows:
        md += f"| {row[0]:<14} | " + " | ".join(f"{cell}" for cell in row[1:]) + " |\n"
    return md

def extract_carryover_and_table(tables, announce_title, lotto_type):
    for idx in range(len(tables)):
        table = tables[idx]
        transposed = transpose_table(table)
        if any(CARRYOVER_KEY in row for row in transposed):
            # ✅ 회차 추출 (제목에 포함)
            match = re.search(r"第(\d+)回", transposed[0][0])
            round_label = f"第{match.group(1)}回" if match else "回次不明"

            # ✅ 이월금 파악
            carryover_row = next((r for r in transposed if CARRYOVER_KEY in r[0]), None)
            if not carryover_row:
                return None
            try:
                amount_str = carryover_row[1].replace(",", "").replace("円", "")
                amount = int(amount_str)
            except Exception:
                amount = 0

            if amount > 0:
                table_markdown = format_markdown_table(transposed)
                return {
                    "lotto_type": lotto_type,
                    "carryover": amount,
                    "round": round_label,
                    "markdown": table_markdown,
                    "announce_date": announce_title,
                }
    return None

def create_github_issue_if_needed(result):
    if not result:
        print("✅ 해당 날짜에는 이월금이 없습니다.")
        return

    title = f"{result['round']} {result['lotto_type']} {result['carryover'] // 10000:,}万円 繰越金発生"
    body = (
        f"🗓️ 発表日: **{result['announce_date']}**\n\n"
        f"💰 **繰越金あり！**\n\n"
        f"{result['markdown']}"
    )

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # 중복 이슈 방지
    existing_titles = [i.title for i in repo.get_issues(state='open')]
    if title in existing_titles:
        print("⚠️ 이미 동일한 이슈가 존재합니다. 생성하지 않음.")
        return

    issue = repo.create_issue(title=title, body=body)
    print("✅ GitHub 이슈가 성공적으로 생성되었습니다.")
    print(f"📌 {issue.html_url}")

def main():
    soup = fetch_html()
    sections = extract_sections(soup)
    tables = extract_tables(soup)

    print(f"📊 감지된 발표일 섹션 수: {len(sections)}")
    print(f"📊 감지된 결과 테이블 수: {len(tables)}\n")

    for idx, sec in enumerate(sections):
        title_text = sec.get_text(strip=True)
        if not is_date_in_text(TARGET_DATE, title_text):
            continue

        # 종목 이름 추출
        match = re.search(r"(toto|mini toto-A|mini toto-B|toto GOAL3)", title_text)
        lotto_type = match.group(1) if match else f"종류불명_{idx}"

        print(f"🧩 [{lotto_type}] 結果発表日: {TARGET_DATE}")

        start_table_idx = idx * 2
        local_tables = tables[start_table_idx:start_table_idx + 2]
        result = extract_carryover_and_table(local_tables, TARGET_DATE, lotto_type)
        create_github_issue_if_needed(result)

if __name__ == "__main__":
    main()
