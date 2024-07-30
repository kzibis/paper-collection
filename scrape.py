import os
import random
import requests
from bs4 import BeautifulSoup
import csv
import time

# Define the filter conditions
filter_conditions = [
    "biochemistry",
    "biotechnology",
    "cancer",
    "cell-biology",
    "chemistry",
    "computational-biology-and-bioinformatics",
    "diseases",
    "endocrinology",
    "engineering",
    "environmental-sciences",
    "environmental-social-sciences",
    "genetics",
    "health-care",
    "immunology",
    "materials-science",
    "medical-research",
    "molecular-biology",
    "neuroscience",
    "risk-factors",
    "water-resources",
    "biological-techniques",
    "biophysics",
    "chemical-biology",
    "developmental-biology",
    "microbiology",
    "nanoscience-and-technology",
    "optics-and-photonics",
    "systems-biology"
]

# Function to extract target IDs from HTML
def extract_target_ids(html):
    soup = BeautifulSoup(html, 'html.parser')
    ids = set()
    for input_tag in soup.find_all('input', {'type': 'checkbox'}):
        if 'id' in input_tag.attrs:
            id_value = input_tag.attrs['id'].replace('subject-', '')
            ids.add(id_value)
    return ids

# Function to get the last page number
def get_last_page_number(soup):
    pagination = soup.find('ul', class_='c-pagination')
    if pagination:
        pages = pagination.find_all('li', class_='c-pagination__item')
        # Find the last page number which should be the second-to-last item in the pagination list
        last_page = pages[-2].text.strip()  # Ensure to strip any surrounding whitespace
        # Extract the numeric part of the page number
        try:
            return int(last_page.replace('page ', ''))
        except ValueError:
            return 1
    return 1

# Function to fetch and parse articles
def fetch_articles(filter_condition, query):
    page_number = 1
    while True:
        url = f'https://www.nature.com/search?q={query}&subject={filter_condition}&order=relevance&page={page_number}'
        print(f'Fetching {url}')
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get the last page number for this filter condition if it's the first page
            if page_number == 1:
                last_page_num = get_last_page_number(soup)
                print(f'Last page number for {filter_condition}: {last_page_num}')

            articles = []
            for article in soup.find_all('a', class_='c-card__link'):
                href = article.get('href')
                title = article.text.strip()
                description = article.find_next('div', class_='c-card__summary')
                description_text = description.get_text(strip=True) if description else ''
                authors = [author.text.strip() for author in soup.find_all('span', itemprop='name')]
                date_published = soup.find('time', class_='c-meta__item')
                date_text = date_published.get_text(strip=True) if date_published else ''

                articles.append({
                    'href': href,
                    'title': title,
                    'description': description_text,
                    'authors': ', '.join(authors),
                    'date_published': date_text
                })

            # Define the directory and file path
            directory = f'result/nature/{query}'
            os.makedirs(directory, exist_ok=True)  # Create the directory if it does not exist
            file_name = f'{directory}/articles_{filter_condition}.csv'
            
            # Check if file exists and write header conditionally
            file_exists = os.path.isfile(file_name)
            with open(file_name, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['href', 'title', 'description', 'authors', 'date_published'])
                if not file_exists:
                    writer.writeheader()  # Write header only if file does not exist
                writer.writerows(articles)

            # Write finished URL to log file
            with open(os.path.join(directory, 'execution_finished_urls.csv'), mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([url])

            # Stop if we have reached the last page
            if last_page_num and page_number >= last_page_num:
                break

            # Move to the next page
            page_number += 1
            time.sleep(3 + (5 - 3) * random.random())  # Delay between 3 to 5 seconds

        except Exception as e:
            # Log error details
            with open(os.path.join(directory,'error_log.csv'), mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([url, str(e)])
            print(f'Error fetching {url}: {e}')

# Function to process all filter conditions sequentially
def process_filter_conditions(query):
    for condition in filter_conditions:
        fetch_articles(condition, query)
        time.sleep(3 + (5 - 3) * random.random())  # Delay between 3 to 5 seconds between filter conditions

# Run the scraper
query = "bioremediation"
process_filter_conditions(query)
