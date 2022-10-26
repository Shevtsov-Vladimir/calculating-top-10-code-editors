# imports


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
import pandas
import time
import os


# sources


FILE_W_NAMES_OF_EDITORS = "/home/user/PycharmProjects/pythonProject/names/titles.txt"
GOOGLE_DATAFILE = '/home/user/PycharmProjects/pythonProject/multiTimeline/multiTimeline.csv'


# class definition


class SiteGoogleTrends:
    # provide work with Google trends site
    def __init__(self):
        # default download directory
        self.prefs = {"download.default_directory": "/home/user/PycharmProjects/pythonProject/multiTimeline"}

        # webdriver options
        self.options = Options()
        # self.options.headless = True
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("prefs", self.prefs)
        self.options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0')
        # self.options.add_experimental_option("detach", True)

        # reference to the webdriver
        self.service = Service(executable_path='/home/user/PycharmProjects/pythonProject/venv/bin/chromedriver')
        # create object of webdriver
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

        # wait object
        self.wait = WebDriverWait(self.driver, 3)

        # css selectors
        self.download_btn_selector = "//button[@class='widget-actions-item export']"
        self.chart_css_selector = 'line-chart-directive[class="fe-line-chart-directive no-legend bar-chart"]'

    def launch_browser(self):
        self.driver.get('https://google.com/')

    def open_google_trends_website(self):
        self.driver.get('https://trends.google.com/trends/explore')

    def make_a_request(self, search_query):
        self.driver.get(search_query)

    def get_datafile(self):
        try:
            self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, self.chart_css_selector)))
            download = self.wait.until(ec.element_to_be_clickable((By.XPATH, self.download_btn_selector)))
            download.click()
            time.sleep(2)
        except (ElementClickInterceptedException, NoSuchElementException, TimeoutException,
                StaleElementReferenceException):
            self.driver.refresh()
            self.get_datafile()

    def close_google_trends(self):
        self.driver.quit()


# functions definition


def titles_quantity(array):
    return sum(map(lambda i: len(i), array))


def top_list_update(dictionary, top_list):
    i = 10

    if len(top_list) > 10:
        return top_list

    if len(top_list) > 0:
        i = 10 - titles_quantity(top_list)

    top_list.append({})

    for key in dictionary:
        if i == 0:
            break
        top_list[-1][key] = dictionary[key]
        i -= 1

    return top_list


def print_top_list(top_list):
    top_list = map(lambda i: '\n'.join(i.keys()), top_list)

    for e in top_list:
        print(e)


def sort_dict(dictionary):
    return dict(sorted(dictionary.items(), key=lambda item: item[1], reverse=True))


def extract_names_of_code_editors(source):
    with open(source, 'r') as file:
        result_arr = file.read().split("\n")
        return result_arr


def remove_google_datafile():
    os.remove(GOOGLE_DATAFILE)


def make_search_query(array):
    search_query = ('https://trends.google.com/trends/explore?cat=730&q='
                    + ','.join(array).replace(' ', '%20').replace("'", '%27').replace('+', '%2B')
                    )
    return search_query


def compare_editors(list_of_titles, top_list, ruler=False, has_recurred=False):
    titles_for_next_comparison = []
    dict_of_average_values = {}
    has_passed = False
    if not ruler:
        ruler = list_of_titles[0]
    work_list = [ruler]
    gt = SiteGoogleTrends()

    gt.launch_browser()
    gt.open_google_trends_website()

    while True:
        try:
            for e in list_of_titles:

                if e == ruler:
                    continue

                work_list.append(e)

                if len(work_list) == 5 or list_of_titles[-1] == work_list[-1]:

                    search_query = make_search_query(array=work_list)
                    gt.make_a_request(search_query=search_query)
                    gt.get_datafile()

                    cols = list(range(1, len(work_list) + 1))
                    df = pandas.read_csv(filepath_or_buffer=GOOGLE_DATAFILE, header=0, skiprows=2, names=[*work_list],
                                         usecols=[*cols])

                    for i in work_list:
                        if has_passed and i == ruler:
                            continue

                        df_list = df[i].tolist()

                        if all(isinstance(n, str) for n in df_list) or max(df_list) < 10 or df_list.count(0) == len(
                                df_list):
                            titles_for_next_comparison.append(i)
                            continue
                        elif max(df_list) == 100 and i != has_recurred and i != list_of_titles[0]:
                            ruler = i
                            has_recurred = i
                            remove_google_datafile()
                            gt.close_google_trends()
                            returned_list = compare_editors(list_of_titles, top_list, ruler,
                                                            has_recurred)
                            return returned_list

                        dict_of_average_values[i] = round(sum(df_list) / len(df_list))

                        has_passed = True

                    remove_google_datafile()

                    work_list = [ruler]

        except NoSuchElementException:
            gt.close_google_trends()
            returned_list = compare_editors(list_of_titles, top_list, ruler,
                                            has_recurred)
            return returned_list

        dict_of_average_values = sort_dict(dict_of_average_values)

        top_list = top_list_update(dict_of_average_values, top_list)

        gt.close_google_trends()
        del gt
        return [titles_for_next_comparison, top_list]


def main():
    titles_for_comparison = extract_names_of_code_editors(source=FILE_W_NAMES_OF_EDITORS)
    top_ten_editors = []

    while titles_quantity(top_ten_editors) < 10 and len(titles_for_comparison) > 1:
        returned_list = compare_editors(titles_for_comparison, top_ten_editors)
        titles_for_comparison = returned_list[0]
        top_ten_editors = returned_list[1]

    print_top_list(top_ten_editors)


if __name__ == '__main__':
    main()
