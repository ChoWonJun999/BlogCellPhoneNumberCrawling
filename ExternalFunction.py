import random
import re
import time
import requests

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import VO


def phExtract(blog_intro_block, id_ph_set):
    patterns = []
    if VO.ph_010:
        patterns.append(r'(010)[^0-9]?(\d{4})[^0-9]?(\d{4})')

    if VO.ph_area:
        patterns.append(
            r'(02|031|032|033|041|042|043|044|051|052|053|054|055|061|062|063|064)[^0-9]?(\d{3,4})[^0-9]?(\d{4})')

    if VO.ph_special:
        patterns.append(r'(030|050|060|070|080)[^0-9]?(\d{4})[^0-9]?(\d{4})')
        patterns.append(
            r'(1588|1577|1899|1544|1644|1661|1566|1600|1670|1688|1666|1599|1877|1855|1800|1541|1633|08217|1655|1677|1682)[^0-9]?(\d{4})')

    for pattern in patterns:
        matches = re.findall(pattern, blog_intro_block)
        for match in matches:
            joined_match = ''.join(match)
            numbers = re.sub(r'\D', '', joined_match)
            if len(numbers) in range(9, 12) or len(numbers) == 8:
                formatted_number = format_phone_number(match)
                before = len(id_ph_set)
                id_ph_text = (VO.blog_id, formatted_number)
                id_ph_set.add(id_ph_text)
                after = len(id_ph_set)
                if before == after:
                    return False
                VO.cleaned_phone_number = formatted_number
                return True

    return False


def format_phone_number(parts):
    # 구분자 제거 및 '-'로 포맷팅, 특수 번호(4자리)는 '-' 없이 연결
    parts = [part.replace(' ', '').replace('/', '').replace('.', '') for part in parts]
    if len(parts) == 1 and len(parts[0]) == 4:
        return parts[0]  # 특수 번호는 '-' 없이 반환
    return '-'.join(parts)


def get_random_user_agent():
    ur = None
    try:
        user_agent = UserAgent()
        ur = user_agent.random
    except Exception as e:
        print(e)
    return ur


def replay(scroll, base_url, max_count, href_list):
    url = f'{base_url}&start={max_count + 1}'
    response = requestSession(url, True)
    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            li_attributes = soup.select('ul.lst_view li')
            if len(li_attributes) == 0:
                return href_list, max_count, True

            for li in li_attributes:
                href_attributes = li.select('div.user_box div.user_box_inner div.user_info a')
                if len(href_attributes) > 0:
                    href = href_attributes[0]
                    blog_url = href['href']
                    print(blog_url)
                    if "adcr.naver.com" not in blog_url and "post.naver.com" not in blog_url and "in.naver.com" not in blog_url:
                        blog_url = blog_url.replace("https://", "https://m.")
                        href_list.append(blog_url)
                        max_count += 1
            return href_list, max_count, False
        except Exception as e:
            print(e)
            return href_list, max_count, False
    else:
        print(f"HTTP 요청에 실패했습니다. 상태 코드: {response.status_code}")
        return replay(scroll, base_url, max_count, href_list)


def requestSession(url, timeSleepChk):
    headers = {'User-Agent': get_random_user_agent()}

    with requests.Session() as session:
        response = session.get(url, headers=headers)
        if timeSleepChk:
            timeSleep()
        return response


def timeSleep():
    chk = random.uniform(0, 10)
    if chk < 6.5:
        time.sleep(random.uniform(0.5, 1.5))
