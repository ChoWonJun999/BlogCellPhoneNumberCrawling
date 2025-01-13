import sys

import atexit
import tkinter as tk
from tkinter import filedialog
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QCheckBox, QSpinBox, QComboBox, \
    QRadioButton, QPushButton, QLineEdit, QPlainTextEdit, QGridLayout
from PyQt5.QtCore import QTimer

from Worker import Worker
import VO


class main(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = None
        self.phone_number_label = QLabel('핸드폰 번호')
        self.phone_number_checkbox_010 = QCheckBox('핸드폰 번호(010)')
        self.phone_number_checkbox_area = QCheckBox('지역 번호')
        self.phone_number_checkbox_special = QCheckBox('특수 번호')
        self.phone_number_checkbox_010.setChecked(True)

        self.visitor_avg_checkbox = QCheckBox('5일 평균 방문자수')
        self.visitor_avg_checkbox.setChecked(True)
        self.visitor_avg_minbox = QSpinBox()
        self.visitor_avg_minbox.setMinimum(1)
        self.visitor_avg_minbox.setMaximum(100000)
        self.visitor_avg_minbox.setValue(10)
        self.visitor_avg_swung_dash = QLabel('~')
        self.visitor_avg_maxbox = QSpinBox()
        self.visitor_avg_maxbox.setMinimum(1)
        self.visitor_avg_maxbox.setMaximum(100000)
        self.visitor_avg_maxbox.setValue(100)

        self.search_option_label = QLabel('검색 옵션')
        self.search_option_combobox = QComboBox()
        self.search_option_combobox.addItems(['관련도순', '최신순'])

        self.blogger_count_label = QLabel('블로거 추출 개수')
        self.blogger_count_spinbox = QSpinBox()
        self.blogger_count_spinbox.setMinimum(1)
        self.blogger_count_spinbox.setMaximum(100000)
        self.blogger_count_spinbox.setValue(100)

        self.blogger_max_label = QLabel('블로거 최대 페이지')
        self.blogger_max_spinbox = QSpinBox()
        self.blogger_max_spinbox.setMinimum(1)
        self.blogger_max_spinbox.setMaximum(100)
        self.blogger_max_spinbox.setValue(30)

        self.extraction_option_label1 = QLabel('추출 옵션')
        self.extraction_option_radio1 = QRadioButton('엑셀')
        self.extraction_option_radio1.setChecked(True)
        self.extraction_option_radio2 = QRadioButton('텍스트')

        # self.disable_crawling_checkbox = QCheckBox('크롤링 끄기')
        # self.disable_crawling_checkbox.setChecked(True)

        path_text = ""
        try:
            file = open("PathText.txt", "r")
            file_read = file.readlines()
            if len(file_read) > 0:
                path_text = file_read[0]
            file.close()
        except Exception as e:
            print(e)

        self.remember_location_checkbox = QCheckBox('저장 위치 기억')
        if path_text == "":
            self.remember_location_checkbox.setChecked(False)
            path_text = "C:/"
        else:
            self.remember_location_checkbox.setChecked(True)

        self.save_path_label = QLabel('저장 위치')
        self.save_path_input = QLineEdit(path_text)
        self.save_path_input.setReadOnly(True)
        self.save_path_button = QPushButton('선택')
        self.save_path_button.clicked.connect(self.choose_save_path)

        # 키워드 입력 부분
        self.keyword_label = QLabel('추출 희망 키워드 입력')
        self.keyword_input1 = QPlainTextEdit()
        self.keyword_input2 = QPlainTextEdit()
        self.keyword_input2.setReadOnly(True)
        self.count_label = QLabel('대기 중...')

        # 추출하기 버튼
        self.extract_button = QPushButton('추출하기')
        # self.extract_button.clicked.connect(self.to_extract)
        self.extract_button.clicked.connect(self.toggleButton)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.enableButton)
        self.is_running = False

        layout = QGridLayout()
        layout.addWidget(self.phone_number_checkbox_010, 0, 0)
        layout.addWidget(self.phone_number_checkbox_area, 0, 1)
        layout.addWidget(self.phone_number_checkbox_special, 0, 2)

        layout.addWidget(self.visitor_avg_checkbox, 1, 0)
        layout.addWidget(self.visitor_avg_minbox, 1, 1)
        layout.addWidget(self.visitor_avg_swung_dash, 1, 2)
        layout.addWidget(self.visitor_avg_maxbox, 1, 3)

        layout.addWidget(self.blogger_count_label, 3, 0)
        layout.addWidget(self.blogger_count_spinbox, 3, 1)
        layout.addWidget(self.blogger_max_label, 3, 2)
        layout.addWidget(self.blogger_max_spinbox, 3, 3)

        layout.addWidget(self.search_option_label, 4, 0)
        layout.addWidget(self.search_option_combobox, 4, 1)
        # layout.addWidget(self.disable_crawling_checkbox, 4, 0)
        layout.addWidget(self.remember_location_checkbox, 4, 3)

        layout.addWidget(self.save_path_input, 5, 0, 1, 3)
        layout.addWidget(self.save_path_button, 5, 3)

        layout.addWidget(self.keyword_label, 6, 0)
        layout.addWidget(self.count_label, 6, 3)
        layout.addWidget(self.keyword_input1, 7, 0, 1, 0)
        layout.addWidget(self.keyword_input2, 8, 0, 1, 0)
        layout.addWidget(self.extract_button, 9, 0, 1, 0)

        self.setLayout(layout)
        self.setMinimumSize(512, 512)
        self.setWindowTitle('블로그 핸드폰 번호 크롤링')

    def choose_save_path(self):
        root = tk.Tk()
        root.withdraw()
        if self.save_path_input.text() == "":
            path_text = "C:/"
        else:
            path_text = self.save_path_input.text()
        file_path = filedialog.askdirectory(initialdir=path_text)  # 디렉토리 선택 대화 상자 열기
        if not file_path:
            file_path = "C:/"

        self.save_path_input.setText(file_path)
        root.destroy()  # Tkinter 창 닫기

    def toggleButton(self):
        if not self.is_running:
            sender = self.sender()  # 이벤트를 보낸 위젯 가져오기
            if sender.text() == "추출하기":
                if not self.phone_number_checkbox_010.isChecked() and not self.phone_number_checkbox_area.isChecked() and not self.phone_number_checkbox_special.isChecked():
                    self.keyword_input2.appendPlainText("핸드폰 번호 출력 형태를 선택하세요.")
                    self.keyword_input2.verticalScrollBar().setValue(self.keyword_input2.verticalScrollBar().maximum())
                    return

                sender.setText("종료하기")
                self.keyword_input1.setReadOnly(True)
                self.extract_button.setEnabled(False)
                self.to_extract()
            elif sender.text() == "종료하기":
                sender.setText("추출하기")
                self.keyword_input1.setReadOnly(False)
                self.extract_button.setEnabled(False)
                self.to_exit()

            self.timer.start(3000)

    def enableButton(self):
        self.is_running = False
        self.extract_button.setEnabled(True)

    def to_extract(self):
        self.keyword_input2.clear()
        
        # 핸드폰 출력 형태
        # 010
        VO.ph_010 = self.phone_number_checkbox_010.isChecked()
        # 지역 번호(02, 031, 032 ...)
        VO.ph_area = self.phone_number_checkbox_area.isChecked()
        # 특수 번호(030, 050 ... / 1588, 1577 ...)
        VO.ph_special = self.phone_number_checkbox_special.isChecked()
        
        # 5일 평균 방문자 수 (1~10000)
        VO.visitor_avg_min_value = -1
        VO.visitor_avg_max_value = -1
        if self.visitor_avg_checkbox.isChecked():
            VO.visitor_avg_min_value = self.visitor_avg_minbox.value()
            VO.visitor_avg_max_value = self.visitor_avg_maxbox.value()

        # 검색 옵션 (관련도 순 / 최신 순)
        VO.search_option_value = self.search_option_combobox.currentText()
        
        # 블로거 추출 개수 (1~10000)
        VO.blogger_count_value = self.blogger_count_spinbox.value()

        # 블로거 최대 페이지 (1~30)
        VO.blogger_max_spinbox = self.blogger_max_spinbox.value()
        
        # 크롤링 끄기
        # VO.disable_value = self.disable_crawling_checkbox.isChecked()

        # 저장 위치 기억
        VO.location_value = self.remember_location_checkbox.isChecked()

        # 파일 저장 위치 기억
        if self.remember_location_checkbox.isChecked():
            file = open("PathText.txt", "w")
            file.write(self.save_path_input.text())
            file.close()
        else:
            file = open("PathText.txt", "w")
            file.close()
        # 파일 경로
        VO.save_path_value = self.save_path_input.text()

        keywords = self.keyword_input1.toPlainText().split("\n")
        cleaned_keywords = [keyword.strip() for keyword in keywords if keyword.strip()]
        VO.keywords = cleaned_keywords

        # Worker 인스턴스를 생성하고 작업을 시작합니다.
        self.worker = Worker()
        # Worker에서 발생하는 phone_number_signal 신호를 메인 윈도우의 add_data 메서드에 연결합니다.
        self.worker.crawling_log_add.connect(self.add_data)
        self.worker.crawling_log_undo.connect(self.cut_data)
        self.worker.crawling_count.connect(self.add_count)
        # Worker를 시작하여 크롤링을 백그라운드에서 시작합니다.
        self.worker.start()

    def to_exit(self):
        self.worker.stop()

    def add_data(self, data):
        self.keyword_input2.appendPlainText(data)
        self.keyword_input2.verticalScrollBar().setValue(self.keyword_input2.verticalScrollBar().maximum())
        if data.split("]")[1].replace(" ", "") == "모든추출이완료됐습니다.":
            self.extract_button.setText("추출하기")
            self.keyword_input1.setReadOnly(False)
            self.count_label.setText("대기 중...")

    def cut_data(self):
        self.keyword_input2.undo()

    def add_count(self, data):
        self.count_label.setText(data)

    def getWorker(self):
        return self.worker


def on_exit(main_instance):
    worker = main_instance.getWorker()
    if worker is not None:
        worker.running = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_instance = main()
    main_instance.show()
    atexit.register(on_exit, main_instance)
    sys.exit(app.exec_())
