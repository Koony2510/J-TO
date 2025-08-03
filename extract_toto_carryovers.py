from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os

# 테스트 날짜 (결과 검증을 위해 고정)
target_date = "2025.08.02"

# GitHub 설정
github_repo = os.getenv("GITHUB_REPOSITORY")
github_token = os.getenv("GITHUB_TOKEN")
github_assignees = ["Koony2510"]
github_mentions = ["Koony2510"]

# 대상 URL
url = "http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 결과 발표일 테이블과 당첨 결과 테이블 짝지어 추출
date_sections = soup.find_all("table", class_="format1 mb5")
result_tables = soup.find_all("table", class_="kobetsu-format2 mb10")

lottery_names = ["toto", "mini toto-A", "mini toto-B", "toto GOAL3"]
carryover_results = []

print(f"\n📊 감지된 발표일 섹션 수: {len(date_sections)}")
print(f"📊 감지된 결과 테이블 수: {len(result_tables)}")

for i in range(len(date_sections)):
    if i >= len(lottery_names) or i >= len(result_tables):
        break

    # 날짜 파싱
    date_table = date_sections[i]
    result_table = result_tables[i*2]  # 주의! 종목당 결과 테이블이 2개임. 1개는 header용

    if "結果発表日" not in date_table.text:
        continue
    result_date = date_table.find_all("td")[-1].get_text(strip=True)
    formatted_date = result_date.replace("年", ".").replace("月", ".").split("日")[0]

    if formatted_date != target_date:
        continue

    print(f"\n🧩 [{lottery_names[i]}] 結果発表日: {formatted_date}")

    rows = result_table.find_all("tr")
    carryover_amount = ""
    carryover_found = False

    # 첫 번째 열이 당첨 등수 (행 이름)임 → 이월금은 열 이름에 있음
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    carryover_index = headers.index("次回への繰越金") if "次回への繰越金" in headers else -1

    if carryover_index == -1:
        continue

    for row in rows[1:]:
        cols = row.find_all("td")
        if not cols or "1等" not in cols[0].text:
            continue
        carryover_amount = cols[carryover_index].get_text(strip=True)
        print(" | ".join(td.get_text(strip=True) for td in cols))
        if carryover_amount != "0円":
            carryover_found = True
            break

    if carryover_found:
        amount_num = int(carryover_amount.replace(",", "").replace("円", ""))
        if amount_num >= 100000000:
            short = f"{amount_num // 100000000}億円"
        elif amount_num >= 10000:
            short = f"{amount_num // 10000}万円"
        else:
            short = carryover_amount

        carryover_results.append({
            "name": lottery_names[i],
            "amount": carryover_amount,
            "short": short,
            "table": result_table
        })

# 이슈 생성
if carryover_results:
    issue_title = " / ".join([f"{r['name']} {r['short']} 移越発生" for r in carryover_results])
    body_lines = []

    for result in carryover_results:
        body_lines.append(f"### 🎯 {result['name']} (次回への繰越金: {result['amount']})")
        body_lines.append("| 등수 | 당첨금 | 당첨수 | 次回への繰越金 |")
        body_lines.append("|------|--------|--------|----------------|")

        for row in result['table'].find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 4:
                texts = [c.get_text(strip=True) for c in cols]
                body_lines.append("| " + " | ".join(texts) + " |")
        body_lines.append("")

    body_lines.append("📎 출처: [toto 공식 페이지](http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp)")

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
        res = requests.post(f"https://api.github.com/repos/{github_repo}/issues", headers=headers, json=payload)
        if res.status_code == 201:
            print("\n✅ GitHub 이슈가 성공적으로 생성되었습니다.")
        else:
            print(f"\n⚠️ GitHub 이슈 생성 실패: {res.status_code} - {res.text}")
    else:
        print("\n⚠️ 환경변수 GITHUB_REPOSITORY 또는 GITHUB_TOKEN 이 설정되지 않았습니다.")
else:
    print("\n✅ 해당 날짜에는 이월금이 없습니다.")
