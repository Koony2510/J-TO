from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os

# 날짜 고정 (테스트용)
target_date = "2025.08.02"

# GitHub 설정
github_repo = os.getenv("GITHUB_REPOSITORY")
github_token = os.getenv("GITHUB_TOKEN")
github_assignees = ["Koony2510"]
github_mentions = ["Koony2510"]

# URL 설정
url = "http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 결과발표일 기준 섹션 구분
sections = []
for date_table in soup.find_all("table", class_="format1 mb5"):
    if "結果発表日" in date_table.text:
        result_date_td = date_table.find_all("td")[-1]
        result_date_text = result_date_td.get_text(strip=True)
        formatted_date = result_date_text.replace("年", ".").replace("月", ".").split("日")[0]
        sections.append((formatted_date, date_table))

# 모든 kobetsu-format2 추출
tables = soup.find_all("table", class_="kobetsu-format2 mb10")

print(f"\n📊 감지된 발표일 섹션 수: {len(sections)}")
print(f"📊 감지된 결과 테이블 수: {len(tables)}\n")

toto_names = ["toto", "mini toto-A", "mini toto-B", "toto GOAL3"]
carryover_results = []
table_index = 0

for i, (date_str, _) in enumerate(sections):
    if date_str != target_date:
        continue

    print(f"\n🧩 [{toto_names[i]}] 結果発表日: {date_str}")

    if table_index + 1 >= len(tables):
        continue

    # table1이 실제 결과 테이블인지 검사
    header_check = tables[table_index].find("tr")
    if header_check and "等級" not in header_check.get_text():
        print(f"⚠️ [무시] table_index {table_index} 는 경기 정보용 테이블로 추정됨. 다음 테이블 사용.")
        table_index += 1

    if table_index >= len(tables):
        continue

    table1 = tables[table_index]      # 등급, 당첨수, 당첨금, 이월금
    table2 = tables[table_index + 1]  # 경기결과용, 무시

    # 첫 번째 테이블에서 정보 추출
    rows = table1.find_all("tr")
    grid = []
    for row in rows:
        cols = row.find_all(["th", "td"])
        grid.append([c.get_text(strip=True) for c in cols])

    found = False
    carryover_amount = ""

    # 전치
    transposed = list(map(list, zip(*grid)))
    print("[🔍 전치 테이블 구조 확인]")
    for line in transposed:
        print(" | ".join(line))

    for col in transposed:
        if col[0] == "等級" and "1等" in col:
            index_1st = col.index("1等")
            for row in grid:
                if row[0] == "次回への繰越金" and len(row) > index_1st:
                    carryover = row[index_1st]
                    print(f"1等 이월금: {carryover}")
                    if carryover != "0円":
                        found = True
                        carryover_amount = carryover
                        break

    if found:
        amount_num = int(carryover_amount.replace(",", "").replace("円", ""))
        if amount_num >= 100000000:
            short = f"{amount_num // 100000000}億円"
        else:
            short = f"{amount_num // 10000}万円"

        carryover_results.append({
            "name": toto_names[i],
            "amount": carryover_amount,
            "short": short,
            "table": table1
        })

    table_index += 2

# 이월금 결과 정리
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

    body_lines.append("📎 출처: [スポーツくじ公式](http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp)")

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
        r = requests.post(f"https://api.github.com/repos/{github_repo}/issues", headers=headers, json=payload)
        if r.status_code == 201:
            print("\n✅ GitHub 이슈가 성공적으로 생성되었습니다.")
        else:
            print(f"\n⚠️ GitHub 이슈 생성 실패: {r.status_code} - {r.text}")
    else:
        print("\n⚠️ 환경변수 GITHUB_REPOSITORY 또는 GITHUB_TOKEN 이 설정되지 않았습니다.")
else:
    print("\n✅ 해당 날짜에는 이월금이 없습니다.")
