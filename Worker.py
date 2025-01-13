import random
import re
import datetime
import time

from PyQt5.QtCore import QThread, pyqtSignal

from bs4 import BeautifulSoup

import excelModule
import VO
import ExternalFunction as ExFun


class Worker(QThread):
    crawling_log_add = pyqtSignal(str)
    crawling_log_undo = pyqtSignal()
    crawling_count = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        log_text = '[추출 옵션] 핸드폰 번호 출력 형태: '
        if VO.ph_010:
            log_text += f'핸드폰 번호(010) '
        if VO.ph_area:
            if log_text != '[추출 옵션] 핸드폰 번호 출력 형태: ':
                log_text += f', '
            log_text += f'지역 번호 '
        if VO.ph_special:
            if log_text != '[추출 옵션] 핸드폰 번호 출력 형태: ':
                log_text += f', '
            log_text += f'특수 번호 '

        if VO.visitor_avg_min_value != -1:
            log_text += f', 5일 평균 방문자 수: {VO.visitor_avg_min_value} ~ {VO.visitor_avg_max_value} '
        log_text += f', 검색 옵션: {VO.search_option_value}'
        log_text += f', 블로거 추출 개수: {VO.blogger_count_value}'
        if VO.location_value:
            log_text += ', 크롤링 끄기'
        if VO.disable_value:
            log_text += ', 저장 위치 기억'
        log_text += f', 저장 위치: {VO.save_path_value}'
        self.logAdd(log_text)

        log_text = ' 작업을 시작합니다.'
        self.logAdd(log_text)

        if self.chkRunning():
            return

        # 각 키워드에 대하여 크롤링을 수행합니다.
        for keyword in VO.keywords:
            self.crawling_count.emit(f"검색 중...")
            VO.keyword = keyword
            exm = excelModule.main()

            # 네이버 블로그 검색 URL을 구성합니다.
            base_url = f'https://search.naver.com/search.naver?ssc=tab.blog.all&query={keyword}&sm=tab_opt&nso=so%3Ar%2Cp%3Aall'
            if VO.search_option_value == "최신순":
                base_url = f'https://search.naver.com/search.naver?ssc=tab.blog.all&query={keyword}&sm=tab_opt&nso=so%3Add%2Cp%3Aall'

            if self.chkRunning():
                return

            log_text = f' 키워드: {keyword} 검색중...'
            self.logAdd(log_text)

            href_list = []
            max_count = 0
            blogger_count = 0
            early_term_chk = True

            page_start_time = time.time()
            for scroll in range(VO.blogger_max_spinbox):
                href_list, max_count, chk = ExFun.replay(scroll, base_url, max_count, href_list)
                if chk:
                    break
                self.crawling_count.emit(f"0/{str(max_count)}")
                if self.chkRunning():
                    return
            page_end_time = time.time()
            page_elapsed_time = page_end_time - page_start_time
            print(f"페이지 검색 소요 시간: {page_elapsed_time} 초")

            id_ph_set = set()
            main_start_time = time.time()
            for index, href in enumerate(href_list, start=1):
                try:
                    self.crawling_count.emit(f"{str(index)}/{str(max_count)}")
                    if self.chkRunning():
                        return
                    VO.blog_url = href
                    VO.blog_id, VO.visitor_5, VO.visitor_today = self.visitorAvg(href.split("/")[-1])
                    if VO.blog_id is None:
                        break
                    elif VO.blog_id == "":
                        continue

                    # 방문자 수로 인한 제어
                    if VO.visitor_avg_min_value != -1 and (
                            int(VO.visitor_avg_min_value) > VO.visitor_5 or int(
                        VO.visitor_avg_max_value) < VO.visitor_5):
                        log_text = f' {VO.blog_id} 방문자 수 규격 미달로 제외합니다.'
                        self.logAdd(log_text)
                        continue

                    link_response = ExFun.requestSession(VO.blog_url, False)
                    if int(random.uniform(0, 10)) == 5:
                        ExFun.timeSleep()

                    if link_response.status_code == 200:
                        link_soup = BeautifulSoup(link_response.text, 'html.parser')
                        try:
                            buddy_element = link_soup.find('span', class_='buddy__fw6Uo')
                            if buddy_element:
                                buddy_block = buddy_element.get_text()
                                VO.blog_buddy = int(buddy_block.replace("명의 이웃", "").replace(",", ""))
                            else:
                                VO.blog_buddy = 0

                            intro_element = link_soup.find('div', class_='introduce_block__R7PeD')
                            if intro_element:
                                blog_intro_block = intro_element.get_text()
                            else:
                                continue

                            chk = ExFun.phExtract(str(blog_intro_block), id_ph_set)
                            if chk:
                                blogger_count += 1
                                if blogger_count % 10 == 0 and blogger_count != 0:
                                    log_text = f' 현재 추출 완료 개수: {str(blogger_count)}개'
                                    self.logAdd(log_text)

                                VO.blogger_count = blogger_count + 1
                                exm.excelWrite()

                                if blogger_count >= VO.blogger_count_value:
                                    break
                        except Exception as e:
                            if self.chkRunning():
                                exm.excelSave()
                                return
                            self.logAdd("ERROR CODE 3")
                            print("[" + str(datetime.datetime.today()) + "] ERROR CODE 3 : " + str(e))
                    else:
                        print(f"HTTP 요청에 실패했습니다. 상태 코드: {link_response.status_code} url: {VO.blog_url}")
                        self.logAdd(f"HTTP 요청에 실패했습니다. 상태 코드: {link_response.status_code} url: {VO.blog_url}")
                        exm.excelSave()
                        return
                except Exception as e:
                    print(e)
            main_end_time = time.time()
            main_elapsed_time = main_end_time - main_start_time
            print(f"메인 검색 소요 시간: {main_elapsed_time} 초")

            if blogger_count < VO.blogger_count_value:
                early_term_chk = False
                log_text = f' 키워드: {keyword} 추출이 조기 완료 됐습니다. (총 {str(blogger_count)} 개)'
                self.logAdd(log_text)
            if self.running and early_term_chk:
                log_text = f' 키워드: {keyword} 추출이 완료 됐습니다. (총 {str(blogger_count)} 개)'
                self.logAdd(log_text)

            exm.excelSize()
            exm.excelSave()

        log_text = " 모든 추출이 완료 됐습니다."
        self.logAdd(log_text)

    def visitorAvg(self, blog_id):
        # 평균 방문자 수
        if "blogid=" in blog_id:
            blog_id = blog_id.split("=")[-1]
        if blog_id:
            try:
                blog_5day_chk_url = f'https://blog.naver.com/NVisitorgp4Ajax.nhn?blogId={blog_id}'
                response = ExFun.requestSession(blog_5day_chk_url, False)
                if int(random.uniform(0, 10)) == 5:
                    ExFun.timeSleep()
                visitor_sum = 0
                visitor_today = 0
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    visitorcnt_tags = soup.find_all('visitorcnt')
                    for index, visitorcnt_tag in enumerate(visitorcnt_tags, start=1):
                        cnt = visitorcnt_tag['cnt']
                        visitor_sum += int(cnt)
                        visitor_today = int(cnt)
                    return blog_id, int(visitor_sum / 5), int(visitor_today)
                else:
                    print(f"HTTP 요청에 실패했습니다. 상태 코드: {response.status_code} blog_id : {blog_5day_chk_url}")
                    self.logAdd(f"HTTP 요청에 실패했습니다. 상태 코드: {response.status_code} url: {blog_5day_chk_url}")
            except Exception as e:
                if not self.running:
                    self.logAdd(" 크롤링이 강제 종료됐습니다.")
                    return None, -1, -1
                self.logAdd("ERROR CODE 2")
                print("[" + str(datetime.datetime.today()) + "] ERROR CODE 2 : " + str(e))
        return "", 0, 0

    def logAdd(self, msg):
        now = datetime.datetime.today()
        formatted_time = now.strftime("%H:%M:%S")
        self.crawling_log_add.emit("[" + str(formatted_time) + f"] {msg}")

    def chkRunning(self):
        if not self.running:
            self.logAdd(" 크롤링이 강제 종료됐습니다.")
            self.crawling_count.emit(f"대기 중...")
            return True
        else:
            return False
