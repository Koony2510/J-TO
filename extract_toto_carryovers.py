from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os

# 날짜 설정 (오늘 날짜 또는 테스트 날짜)
target_date = "2025.08.02"

# GitHub 설정
github_repo = os.getenv("GITHUB_REPOSITORY")
github_token = os.getenv("GITHUB_TOKEN")
github_assignees = ["Koony2510"]
github_mentions = ["Koony2510"]

# 종목명 설정
toto_names = ["toto", "mini toto-A", "mini toto-B", "toto GOAL3"]

# URL 로드
url = "http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 결과일자 추출
sections = []
for date_table in soup.find_all("table", class_="format1 mb5"):
    if "結果発表日" in date_table.text:
        result_date_td = date_table.find_all("td")[-1]
        result_date_text = result_date_td.get_text(strip=True)
        formatted_date = result_date_text.replace("年", ".").replace("月", ".").split("日")[0]
        sections.append((formatted_date, date_table))

# 모든 결과 테이블 수집
tables = soup.find_all("table", class_="kobetsu-format2 mb10")
print(f"\n📊 감지된 발표일 섹션 수: {len(sections)}")
print(f"📊 감지된 결과 테이블 수: {len(tables)}")

carryover_results = []
table_index = 0

for i, (date_str, _) in enumerate(sections):
    if date_str != target_date:
        table_index += 2  # 각 섹션마다 2개 테이블
        continue

    print(f"\n🧩 [{toto_names[i]}] 結果発表日: {date_str}")

    table = tables[table_index + 1]  # 당첨 결과 테이블 (두 번째 테이블)
    rows = table.find_all("tr")
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

    carry_row = None
    for row in rows:
        if row.find("th") and "次回への繰越金" in row.find("th").text:
            carry_row = row
            break

    if carry_row:
        cells = carry_row.find_all("td")
        if len(cells) >= 1:
            amount = cells[0].get_text(strip=True)
            if amount != "0円":
                amount_num = int(amount.replace(",", "").replace("円", ""))
                if amount_num >= 100000000:
                    short = f"{amount_num // 100000000}億円"
                elif amount_num >= 10000000:
                    short = f"{amount_num // 1000000}万円"
                else:
                    short = f"{amount_num // 10000}万円"

                carryover_results.append({
                    "name": toto_names[i],
                    "amount": amount,
                    "short": short,
                    "table": table
                })

    table_index += 2

# 이월금이 있는 경우 GitHub 이슈 생성
if carryover_results:
    issue_title = " / ".join(
        [f"{item['name']} {item['short']} 移越発生" for item in carryover_results]
    )

    body_lines = []
    for item in carryover_results:
        body_lines.append(f"### 🎯 {item['name']} (次回への繰越金: {item['amount']})")
        rows = item["table"].find_all("tr")
        for row in rows:
            texts = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            body_lines.append(" | ".join(texts))
        body_lines.append("")

    body_lines.append("\n📎 출처: [toto 結果ページ](http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp)")

    if github_repo and github_token:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json"
        }
        payload = {
            "title": issue_title,
            "body": f"{' '.join([f'@{u}' for u in github_mentions])}\n\n" + "\n".join(body_lines),
            "assignees": github_assignees
        }

        response = requests.post(f"https://api.github.com/repos/{github_repo}/issues", headers=headers, json=payload)
        if response.status_code == 201:
            print("\n✅ GitHub 이슈가 성공적으로 생성되었습니다.")
        else:
            print(f"\n⚠️ GitHub 이슈 생성 실패: {response.status_code} - {response.text}")
    else:
        print("\n⚠️ 환경변수 GITHUB_REPOSITORY 또는 GITHUB_TOKEN 이 설정되지 않았습니다.")
else:
    print("\n✅ 해당 날짜에는 이월금이 없습니다.")
