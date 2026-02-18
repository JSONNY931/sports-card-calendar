#!/usr/bin/env python3
"""
스포츠카드 발매 일정 스크래퍼
checklistinsider.com에서 최신 발매 일정을 가져옵니다.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse


def parse_date(date_text):
    """날짜 텍스트를 YYYY-MM-DD 형식으로 변환"""
    months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    match = re.search(r'(\w+)\s+(\d+),\s+(\d+)', date_text)
    if match:
        month, day, year = match.groups()
        month_num = months.get(month)
        if month_num:
            return f"{year}-{month_num}-{day.zfill(2)}"
    return None


def extract_sport_from_url(url):
    """URL에서 스포츠 카테고리 추출"""
    category_map = {
        'basketball': 'basketball',
        'baseball': 'baseball',
        'football': 'football',
        'soccer': 'soccer',
        'hockey': 'hockey',
        'racing': 'racing',
        'wrestling': 'wrestling',
        'golf': 'golf',
        'tennis': 'tennis',
        'mma': 'mma',
        'multi-sport': 'other',
        'non-sport': 'other'
    }

    url_lower = url.lower()
    for category, sport in category_map.items():
        if category in url_lower:
            return sport
    return 'other'


def extract_brand(name):
    """제품명에서 브랜드 추출"""
    brands = ['Panini', 'Topps', 'Upper Deck', 'Donruss', 'Bowman',
              'Fleer', 'Rittenhouse', 'Cryptozoic', 'Leaf']

    for brand in brands:
        if brand.lower() in name.lower():
            return brand
    return 'Unknown'


def scrape_releases():
    """checklistinsider.com에서 발매 일정 스크래핑"""

    list_url = "https://www.checklistinsider.com/release-calendar?v=list"
    base = "https://www.checklistinsider.com"

    try:
        print(f"Fetching data from {list_url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(list_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        releases = []
        seen = set()  # 중복 방지 (date + url)

        # 날짜 헤더 찾기
        date_headers = soup.find_all("h2")

        for header in date_headers:
            date_text = header.get_text(" ", strip=True)

            # TBA 제외
            if date_text.upper() == "TBA":
                continue

            parsed_date = parse_date(date_text)
            if not parsed_date:
                continue

            # 다음 h2 나오기 전까지 모든 요소 탐색
            for elem in header.find_all_next():
                if elem == header:
                    continue

                # 다음 날짜 섹션 만나면 중단
                if getattr(elem, "name", None) == "h2":
                    break

                if getattr(elem, "name", None) != "a":
                    continue

                href = elem.get("href", "")
                if not href:
                    continue

                # 불필요 링크 제외
                if href.startswith("#"):
                    continue
                if "/release-calendar" in href:
                    continue

                # 상대경로 → 절대경로 변환
                full_url = urljoin(base, href)

                # checklistinsider 도메인만 허용
                domain = urlparse(full_url).netloc
                if "checklistinsider.com" not in domain:
                    continue

                name = elem.get_text(" ", strip=True)

                # Guide / Checklist 제거
                name = re.sub(r"\s+(Checklist\s+Guide|Checklist|Guide)\s*$",
                              "", name, flags=re.IGNORECASE).strip()

                if not name or len(name) < 6:
                    continue

                key = (parsed_date, full_url)
                if key in seen:
                    continue
                seen.add(key)

                release = {
                    "date": parsed_date,
                    "sport": extract_sport_from_url(full_url),
                    "name": name,
                    "brand": extract_brand(name),
                    "url": full_url
                }

                releases.append(release)

        print(f"Found {len(releases)} releases")
        return releases

    except Exception as e:
        print(f"Error scraping data: {e}")
        return []


def save_releases_json(releases, filename='releases.json'):
    """발매 일정을 JSON 파일로 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(releases, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(releases)} releases to {filename}")


def main():
    print("Starting scraper...")
    releases = scrape_releases()

    if releases:
        save_releases_json(releases)
        print(f"Successfully scraped {len(releases)} releases!")
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("No releases found or error occurred")
        save_releases_json([])


if __name__ == "__main__":
    main()
