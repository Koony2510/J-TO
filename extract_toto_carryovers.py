from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os

# 오늘 날짜를 'YYYY.MM.DD' 형식으로 설정
target_date = datetime.today().strftime("%Y.%m.%d")

# GitHub 설정
github_repo = os.getenv("GITHUB_REPOSITORY")
github_token = os.getenv("GITHUB_TOKEN")
github_assignees = ["Koony2510"]
github_mentions = ["Koony2510"]

# 로또 웹사이트 URL (toto 시리즈)
url = "http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 발표일 구분 테이블
sections = []
for table in soup.find_all("table", class_="format1 mb5"):
    if "結果発表日" in table.text:
        date_text = table.find_all("td")[-1].get_text(strip=True)
        formatted_date = date_text.replace("年", ".").replace("月", ".").split("日")[0]
        sections.append((formatted_date, table))

# 결과 테이블
all_tables = soup.find_all("table", class_="kobetsu-format2 mb10")

print(f"\n📊 감지된 발표일 섹션 수: {len(sections)}")
print(f"📊 감지된 결과 테이블 수: {len(all_tables)}\n")

lottery_names = ["toto", "mini toto-A", "mini toto-B", "toto GOAL3"]
carryover_results = []
table_index = 0

for i, (date_str, _) in enumerate(sections):
    if date_str != target_date:
        table_index += 2  # 각 섹션당 테이블 2개씩
        continue

    print(f"\n🧩 [{lottery_names[i]}] 結果発表日: {date_str}")

    # 2개의 테이블: 당첨금 및 구입정보
    prize_table = all_tables[table_index]
    rows = prize_table.find_all("tr")
    table_index += 2

    # 표를 전치(transpose)
    grid = []
    for row in rows:
        cols = row.find_all(["th", "td"])
        grid.append([c.get_text(strip=True) for c in cols])

    transposed = list(map(list, zip(*grid)))

    found = False
    carryover = ""

    for row in transposed:
        if len(row) >= 4 and row[0] == "次回への繰越金" and row[1] != "0円":
            carryover = row[1]
            found = True
            break

    if found:
        amount_num = int(carryover.replace(",", "").replace("円", ""))
        if amount_num >= 100000000:
            short = f"{amount_num // 100000000}億円"
        elif amount_num >= 10000000:
            short = f"{amount_num // 1000000}万円"
        else:
            short = f"{amount_num // 10000}万円"

        carryover_results.append({
            "name": lottery_names[i],
            "amount": carryover,
            "short": short,
            "table": prize_table
        })

# 결과 요약 및 GitHub 이슈 생성
if carryover_results:
    issue_title = " / ".join(
        [f"{item['name']} {item['short']} 移越発生" for item in carryover_results]
    )

    body_lines = []
    for item in carryover_results:
        body_lines.append(f"### 🎯 {item['name']} (次回への繰越金: {item['amount']})")
        rows = item["table"].find_all("tr")
        for row in rows:
            cols = row.find_all(["th", "td"])
            texts = [c.get_text(strip=True) for c in cols]
            body_lines.append(" | ".join(texts))
        body_lines.append("")

    body_lines.append("📎 출처: [スポーツくじ toto 公式サイト](http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp)")

    # GitHub 이슈 생성
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
        print("\n⚠️ GITHUB_REPOSITORY 또는 GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
else:
    print("\n✅ 해당 날짜에는 이월금이 없습니다.")
