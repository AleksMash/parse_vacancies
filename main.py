from os import getenv
from statistics import fmean

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


POPULAR_LANGS = ['Python', 'JavaScript', 'Java']
HH_PROF_AREA=1
HH_PROF_ROLE=96
PER_PAGE_LIMIT=100
SJ_MOSCOW_ID=4


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    if not vacancy['salary']:
        return None
    start, end, currency, _ = vacancy['salary'].values()
    if not currency=='RUR':
        return None
    return predict_salary(start, end)


def predict_rub_salary_superJob(vacancy):
    currency = vacancy['currency']
    if not currency or currency != 'rub':
        return None
    start = vacancy['payment_from']
    end = vacancy['payment_to']
    return predict_salary(start, end)


def parse_hh():
    base_url = 'https://api.hh.ru/vacancies'
    headers = {
        'User-Agent': 'MyApp',
    }
    table_output = [
        ['Язык', 'Вкансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]
    for lang in POPULAR_LANGS:
        page, max_page = 0, 1
        all_vacancies=[]
        while page < max_page:
            params = {
                'area': HH_PROF_AREA,
                'professional_role': HH_PROF_ROLE,
                'text': lang,
                'search_field': ['name', 'description'],
                'only_with_salary': True,
                'page': page,
                'per_page': PER_PAGE_LIMIT
            }
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            vacancies_per_page = response.json()
            all_vacancies.extend(vacancies_per_page['items'])
            max_page = vacancies_per_page['pages']
            page += 1
        salaries = list(map(predict_rub_salary_hh, all_vacancies))
        salaries_not_none = list(filter(lambda x: x, salaries))
        avg_salary = fmean(salaries_not_none) if salaries_not_none else 0
        table_output.append([lang, vacancies_per_page['found'],
                         len(salaries_not_none), f'{int(avg_salary):_} руб.'.replace('_', ' ')])
    table = AsciiTable(table_output, 'HeadHunter Moscow')
    print(table.table)


def parse_superjob():
    load_dotenv()
    TOKEN_SJ = getenv('TOKEN_SUPERJOB')
    base_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': TOKEN_SJ}
    table_output = [
        ['Язык', 'Вкансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]
    for lang in POPULAR_LANGS:
        page, max_page = 0, 1
        all_vacancies=[]
        while True:
            params = {
                'town': SJ_MOSCOW_ID,
                'keywords[0][srws]': 1,
                'keywords[0][keys]': 'программист',
                'keyword': lang,
                'page': page,
                'count': PER_PAGE_LIMIT
            }
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            vacancies_per_page = response.json()
            all_vacancies.extend(vacancies_per_page['objects'])
            if vacancies_per_page['more']:
                page += 1
            else:
                break
        salaries = list(map(predict_rub_salary_superJob, all_vacancies))
        salaries_not_none = list(filter(lambda x: x, salaries))
        avg_salary = fmean(salaries_not_none) if salaries_not_none else 0
        table_output.append([lang, vacancies_per_page['total'],
                           len(salaries_not_none), f'{int(avg_salary):_} руб.'.replace('_', ' ')])
    table = AsciiTable(table_output, 'SuperJob Moscow')
    print(table.table)


if __name__=='__main__':
    parse_hh()
    print()
    parse_superjob()