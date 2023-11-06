import logging
from datetime import datetime
import time
import codecs
import json
import requests
from bs4 import BeautifulSoup
import urllib3

english_base_url = "https://www.tn.gov.in/go_view/atoz/All?page="
tamil_base_url = 'https://www.tn.gov.in/ta/go_view/atoz/All?page='
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

department_name = ''    

def extract_go_abstract_info(html_content):
    global department_name
    soup = BeautifulSoup(html_content, 'html.parser')
    go_boxes = soup.find_all('div', class_='go_box')

    go_abstract_info = []
    first_go = True

    for go_box in go_boxes:
        
        if(str(go_box.find('div', class_='res_dept').get_text(strip=True)) != ''):
            department_name = (str(go_box.find('div', class_='res_dept').get_text(strip=True)))
            
        go_abstract_div = go_box.find('div', class_='go_abstract')
        go_link = go_abstract_div.find('a')

        if go_link:
            link_url = go_link['href']
            logging.info(link_url)
            if(link_url == 'http://cms.tn.gov.in/'):
                continue
            link_text = go_abstract_div.find('a').contents[0]
            try:
                if not first_go:
                    link_size = go_link.find('span').contents[3]
                else:
                    link_size = go_link.find('span').find('img').contents[1]
                    first_go = False
            except:
                link_size = None
        else:
            link_url = None
            link_text = None
            link_size = None

        go_abstract_info.append({
            'deptname': department_name,
            'go_text': go_abstract_div.contents[1],            
            'url': link_url,
            'go_number_date': link_text,
            'file_size': link_size
        })

    return go_abstract_info

def get_all_go_in_a_page(url_base, page_num,filename):
    all_go_abstracts = []
    for page_number in range(page_num):
        url = url_base + str(page_number)
        logging.info(url)
        response = requests.get(url, verify=False)

        if response.status_code == 200:
            html_content = response.content
            all_go_abstracts.extend(extract_go_abstract_info(html_content))

        else:
            logging.info(f"Failed to retrieve page {page_number}: {response.status_code}")

        with codecs.open(filename, 'w', encoding='utf-8') as file:
            json.dump(all_go_abstracts, file, indent=4, ensure_ascii=False)

def extract_date(all_gos, lang):
    logging.log(logging.INFO, 'start of extract date for ' + lang)
    cleaned_go = []
    for go in all_gos:
        go['number'] = go['go_number_date'].split(' Dt: ')[0]
        go['go_date'] = go['go_number_date'].split(' Dt: ')[1]
        go['lang'] = lang
        del go['go_number_date']
        cleaned_go.append(go)
    return cleaned_go


def main():
    logging.basicConfig(filename='./logs/GO_Archiver' + time.strftime("%Y%m%d-%H%M%S") + '.log', format='%(asctime)s %(message)s', level=logging.INFO)

    get_all_go_in_a_page(url_base=english_base_url,page_num=390,filename='./data/all_go_english.json')
    get_all_go_in_a_page(url_base=tamil_base_url,page_num=87,filename='./data/all_go_tamil.json')

    all_gos = []
    with codecs.open('./data/all_go_english.json', 'r', encoding='utf-8') as f:
        eng_go = json.load(f)
    with codecs.open('./data/all_go_tamil.json', 'r', encoding='utf-8') as f:
        tam_go = json.load(f)

    all_gos.append(extract_date(eng_go,'English'))
    all_gos.append(extract_date(tam_go,'Tamil'))

    with codecs.open('./data/all_go.json', 'w', encoding='utf-8') as file:
        json.dump(all_gos, file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()