from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from pydantic import BaseModel, Field
from pprint import pprint
from collections import defaultdict
import json

class Mark(BaseModel):
    mark: int = Field(..., ge=2, le=5)
    koef: int = Field(..., ge=0, le=5)


class Module(BaseModel):
    name: str
    marks: list[Mark]

class Subject(BaseModel):
    name: str
    modules: list[Module]


class Driver:
    def __enter__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()
    

    def start_page(self, path):
        self.driver.get(path)
        
    
    def login(self, username, password):
        try:
            WebDriverWait(self.driver, 1000000).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
        except TimeoutException:
            raise TimeoutException("Timeout waiting for login form")
    
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)

        login_button = self.driver.find_element(By.ID, "submit")
        login_button.click()

        try:
            WebDriverWait(self.driver, 1000000).until(
                EC.presence_of_element_located((By.ID, "primal-portal"))
            )
        except TimeoutException:
            raise TimeoutException("Timeout waiting for login success")

    
    def go_to_marks(self):
        self.driver.get(self.driver.current_url.replace('/ediary', '') + "final-marks")

        try:
            WebDriverWait(self.driver, 1000000).until(
                EC.presence_of_element_located((By.CLASS_NAME, "main-block-table"))
            )
        except TimeoutException:
            raise TimeoutException("Timeout waiting for marks page")
    

    def get_marks(self):
        marks_table = lambda: self.driver.find_element(By.CLASS_NAME, "main-block-table").find_element(By.XPATH, './div')
        marks_rows = lambda: marks_table().find_elements(By.XPATH, "./div")

        all_subjects = []
        for subject_id in range(1, len(marks_rows())):

            try:
                elem = marks_rows()[subject_id]
                elem = elem.find_element(By.XPATH, "./div").find_elements(By.XPATH, "./div")
                name = elem[0].text
            except StaleElementReferenceException:
                elem = marks_rows()[subject_id]
                elem = elem.find_element(By.XPATH, "./div").find_elements(By.XPATH, "./div")
                name = elem[0].text
            marks_per_year = lambda: marks_rows()[subject_id].find_element(By.XPATH, "./div").find_elements(By.XPATH, "./div")[1]
            # marks_per_year = elem[1]

            subject = Subject(name=name, modules=self.get_marks_per_subject(marks_per_year, name))
            # pprint(subject.model_dump())
            all_subjects += [subject]

        return all_subjects
    
    def get_marks_per_subject(self, marks_per_year: WebElement, name):
        modules = lambda: marks_per_year().find_elements(By.XPATH, "./div")
        all_modules = []

        for module_id in range(len(modules()) - 1):
            period = modules()[module_id]

            try:
                if period.text == '—':
                    continue
                period.click()
            except StaleElementReferenceException:
                period = modules()[module_id]
                if period.text == '—':
                    continue
                period.click()

            try:
                WebDriverWait(self.driver, 1000000).until(
                    lambda driver: driver.find_element(By.CSS_SELECTOR, "[data-testid='FinalMarks.subject-name-widget']").text == name
                )
            except TimeoutException:
                raise TimeoutException("Timeout waiting for marks page")
            # while True: ...
            all_modules += [Module(name=str(module_id + 1), marks=self.get_marks_per_module())]

        return all_modules

    def get_marks_per_module(self):
        marks = lambda: self.driver.find_elements(By.CLASS_NAME, "grade-block")
        all_marks = []
        for id in range(len(marks())):
            try:
                mark_info = marks()[id]
                mark, koef = mark_info.text.split()
            except StaleElementReferenceException:
                mark_info = marks()[id]
                mark, koef = mark_info.text.split()
            all_marks += [Mark(mark=int(mark), koef=int(koef))]
        return all_marks
        

def get_marks(login, password):
    with Driver() as driver:
        driver.start_page("https://auth.sberclass.ru/auth/realms/EduPowerKeycloak/protocol/openid-connect/auth?response_type=code&client_id=edupower&scope=openid%20profile%20email&redirect_uri=https://beta.sberclass.ru/services/auth/login/oauth2/code/edupower?returnTo%3Dhttps://beta.sberclass.ru/ediary/")
        driver.login(login, password)
        driver.go_to_marks()
        marks: list[Subject] = (driver.get_marks())
        return marks

    # with open("marks.json", "r", encoding="utf-8") as f:
    #     marks: list[Subject] = json.load(f)
    #     for i in range(len(marks)):
    #         marks[i] = Subject.model_validate(marks[i])
    
    # coun = defaultdict(int)
    # for subject in marks:
    #     pprint(subject.model_dump())
    
    # for subject in marks:
    #     for module in subject.modules:
    #         for mark in module.marks:
    #             coun[mark.mark] += mark.koef
    
    # pprint(coun)
    # print((coun[5] * 5 + coun[4] * 4 + coun[3] * 3) / sum(coun.values()))

