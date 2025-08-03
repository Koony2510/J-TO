from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os

# 오늘 날짜를 YYYY.MM.DD 형식으로 변환
target_date = datetime.today().strftime("%Y.%m.%d")

# GitHub 설정
github_repo = os.getenv("GITHUB_REPOSITORY")
github_token = os.getenv("GITHUB_TOKEN")
github_assignees = ["Koony2510"]
github_mentions = ["Koony2510"]

# URL
url = "http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# 날짜 섹션들 찾기
sections = []
for table in soup.find_all("table", class_="format1 mb5"):
    if "結果発表日" in table.text:
        result_date_td = table.find_all("td")[-1]
        result_date_raw = result_date_td.get_text(strip=True)
        formatted_date = result_date_raw.replace("年", ".").replace("月", ".").split("日")[0]
        sections.append(formatted_date)

# 결과 테이블 파싱
all_tables = soup.find_all("table", class_="kobetsu-format2 mb10")
lottery_names = ["toto", "mini toto-A組", "mini toto-B組", "totoGOAL3"]
carryover_results = []

print(f"\n📊 감지된 발표일 섹션 수: {len(sections)}")
print(f"📊 감지된 결과 테이블 수: {len(all_tables)}\n")

for i, table in enumerate(all_tables):
    if i >= len(sections):
        continue
    result_date = sections[i]
    if result_date != target_date:
        continue

    print(f"🧩 [{lottery_names[i]}] 結果発表日: {result_date}")
    rows = table.find_all("tr")
    if len(rows) < 4:
        continue

    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    prize_labels = [td.get_text(strip=True) for td in rows[1].find_all("td")]
    prize_counts = [td.get_text(strip=True) for td in rows[2].find_all("td")]
    carryovers = [td.get_text(strip=True) for td in rows[3].find_all("td")]

    if "1等" in headers:
        idx = headers.index("1等")
        carryover = carryovers[idx]
        if carryover != "0円":
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
                "headers": headers,
                "labels": prize_labels,
                "counts": prize_counts,
                "carryovers": carryovers
            })

# 이슈 작성
if carryover_results:
    issue_title = " / ".join(
        [f"{item['name']} {item['short']} 移越発生" for item in carryover_results]
    )

    body_lines = []
    for item in carryover_results:
        body_lines.append(f"### 🎯 {item['name']} (次回への繰越金: {item['amount']})")
        body_lines.append("| 등수 | 当せん金 | 当せん口数 | 次回への繰越金 |")
        body_lines.append("|------|-----------|--------------|------------------|")
        for i in range(len(item["headers"])):
            if "等" in item["headers"][i]:
                row = f"| {item['headers'][i]} | {item['labels'][i]} | {item['counts'][i]} | {item['carryovers'][i]} |"
                body_lines.append(row)
        body_lines.append("")

    body_lines.append("📎 출처: [toto 결과 페이지](http://www.toto-dream.com/dci/I/IPB/IPB01.do?op=initLotResultDettoto&popupDispDiv=disp)")

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
