from bs4 import BeautifulSoup
import requests
import os

# ✅ 테스트용 날짜 고정
target_date = "2025.08.02"

# GitHub 설정
github_repo = os.getenv("GITHUB_REPOSITORY")
github_token = os.getenv("GITHUB_TOKEN")
github_assignees = ["Koony2510"]
github_mentions = ["Koony2510"]

# URL 접속
url = "http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 결과발표일 섹션 탐색
sections = []
for table in soup.find_all("table", class_="format1 mb5"):
    if "結果発表日" in table.text:
        td = table.find_all("td")[-1]
        raw_date = td.get_text(strip=True)
        formatted = raw_date.replace("年", ".").replace("月", ".").split("日")[0]
        sections.append((formatted, table))

# 결과 테이블 수집
result_tables = soup.find_all("table", class_="kobetsu-format2 mb10")

print(f"\n📊 감지된 발표일 섹션 수: {len(sections)}")
print(f"📊 감지된 결과 테이블 수: {len(result_tables)}\n")

lottery_names = ["toto", "mini toto-A", "mini toto-B", "toto GOAL3"]
carryover_results = []
table_index = 0

for i, (date_str, _) in enumerate(sections):
    if date_str != target_date:
        table_index += 2  # 각 회차에 테이블이 2개씩 있으므로 증가
        continue

    if table_index + 1 >= len(result_tables):
        continue

    table = result_tables[table_index]  # 1등~3등 정보 테이블만 사용
    rows = table.find_all("tr")

    print(f"\n🧩 [{lottery_names[i]}] 結果発表日: {date_str}")
    found = False
    carryover_amount = ""

    for row in rows:
        ths = row.find_all("th")
        tds = row.find_all("td")
        if not ths or not tds:
            continue

        rank = ths[0].get_text(strip=True)
        if "1等" in rank and len(tds) >= 3:
            carryover_amount = tds[2].get_text(strip=True)
            print(f"▶ 1등 이월금: {carryover_amount}")
            if carryover_amount != "0円":
                found = True

    if found:
        amount = carryover_amount
        num = int(amount.replace(",", "").replace("円", ""))
        if num >= 100000000:
            short = f"{num // 100000000}億円"
        elif num >= 10000000:
            short = f"{num // 1000000}万円"
        else:
            short = f"{num // 10000}万円"

        carryover_results.append({
            "name": lottery_names[i],
            "amount": amount,
            "short": short,
            "table": table
        })

    table_index += 2  # 다음 종목으로 이동 (2개 테이블 스킵)

# 이월금이 있을 경우 GitHub 이슈 생성
if carryover_results:
    issue_title = " / ".join(
        [f"{item['name']} {item['short']} 移越発生" for item in carryover_results]
    )

    body_lines = []
    for item in carryover_results:
        body_lines.append(f"### 🎯 {item['name']} (次回への繰越金: {item['amount']})")
        body_lines.append("| 등수 | 当せん金 | 当せん口数 | 次回への繰越金 |")
        body_lines.append("|------|------------|--------------|----------------|")
        for row in item["table"].find_all("tr"):
            ths = row.find_all("th")
            tds = row.find_all("td")
            if ths and tds and "等" in ths[0].get_text(strip=True):
                cells = [th.get_text(strip=True) for th in ths] + [td.get_text(strip=True) for td in tds]
                body_lines.append("| " + " | ".join(cells) + " |")
        body_lines.append("")

    body_lines.append("📎 출처: [toto 결과 페이지](http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp)")

    if github_repo and github_token:
        import requests
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
