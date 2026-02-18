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
        if brand in name:
            return brand
    return 'Unknown'

def scrape_releases():
    """checklistinsider.com에서 발매 일정 스크래핑"""
    url = "https://www.checklistinsider.com/release-calendar?v=list"
    
    try:
        print(f"Fetching data from {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        releases = []
        
        # 날짜별 섹션 찾기
        date_headers = soup.find_all('h2')
        
        for header in date_headers:
            date_text = header.get_text(strip=True)
            
            # TBA 섹션은 건너뛰기
            if date_text == 'TBA':
                continue
            
            # 날짜 파싱
            parsed_date = parse_date(date_text)
            if not parsed_date:
                continue
            
            # 해당 날짜의 제품들 찾기
            next_elem = header.find_next_sibling()
            while next_elem and next_elem.name != 'h2':
                # 링크 찾기
                links = next_elem.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    if 'checklistinsider.com' in href and '/release-calendar' not in href:
                        name = link.get_text(strip=True)
                        # "Guide"나 "Checklist" 제거
                        name = name.replace(' Guide', '').replace(' Checklist', '')
                        name = name.replace(' Checklist Guide', '')
                        
                        if name and len(name) > 5:  # 의미있는 이름만
                            release = {
                                'date': parsed_date,
                                'sport': extract_sport_from_url(href),
                                'name': name,
                                'brand': extract_brand(name),
                                'url': href
                            }
                            releases.append(release)
                
                next_elem = next_elem.find_next_sibling()
        
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
        # 실패 시 빈 배열이라도 저장
        save_releases_json([])

if __name__ == "__main__":
    main()
