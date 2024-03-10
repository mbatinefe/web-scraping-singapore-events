import os, sys, glob, re
import json
from pprint import pprint

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
from config import RAW_HTML_DIR, PARSED_HTML_PATH

# Encoding for writing the parsed data to JSONS file
# Do not change unless you are getting a UnicodeEncodeError
ENCODING = "utf-8"


def extract_content_from_page(file_path):
    """
    This function should take as an input the path to one html file
    and return a dictionary "parsed_data" having the following information:

    parsed_data = {
        "date": Date of the news on the html page
        "title": Title of the news on the html page
        "content": The text content of the html page
        }

    This function is used in the parse_html_pages() function.
    You do not need to modify anything in that function.
    """
    parsed_data = {}

    # WRITE YOUR CODE HERE
    ##################################
    soup = bs(open(file_path, 'r', encoding=ENCODING).read(), 'lxml')

    # Extracting the title
    titlesou = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                   .find('section', {'class': 'body-content'}) \
                   .find('div', {'class': 'innerpage1'}) \
                   .find('h1')
    if titlesou is not None:
        # encode and decode for \u00e2\u20ac\u2122 strings
        parsed_data['title'] = titlesou.text.encode('ascii', 'ignore').decode()
    else:
        parsed_data['title'] = "NULL"

    # Extracting date in the page
    inner1 = soup.find('div', {'class': 'off-canvas-wrapper'}) \
        .find('section', {'class': 'body-content'}) \
        .find('div', {'class': 'innerpage1'}) \
        .find('h2')
    if inner1 is not None:
        inner1 = inner1.get_text()
        inner1 = pd.to_datetime(inner1, errors="coerce").date()
        parsed_data['date'] = str(inner1)

    else:
        inner2opt1 = soup.find('div', {'class': 'off-canvas-wrapper'}) \
            .find('section', {'class': 'body-content'}) \
            .find('div', {'class': 'innerpage2'}) \
            .find('div', {'class': 'text'})

        inner2opt1_last = inner2opt1.text.rsplit('\n')
        inner2opt1_last = [elem for elem in inner2opt1_last if elem]
        inner2opt1_last = inner2opt1_last[-1]  # If date in the end of the list

        inner2opt1_last = pd.to_datetime(inner2opt1_last, errors="coerce").date()

        if not pd.isnull(inner2opt1_last):
            parsed_data['date'] = str(inner2opt1_last)

        else:
            inner2opt2 = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                .find('section', {'class': 'body-content'}) \
                .find('div', {'class': 'innerpage2'}) \
                .find('div', {'class': 'text'}) \
                .find('td', {'colspan': '2'})

            if inner2opt2 is not None:
                inner2opt2_last = inner2opt2.get_text().rsplit('\n')
                inner2opt2_last = [elem for elem in inner2opt2_last if elem]
                inner2opt2_last = inner2opt2_last[0]

                # Range problem Parsed Page Id: 0049db6191f4376fad55931551696011
                # Largest range can be 99 September 9999 with range 17 + 1 (error point)
                if len(inner2opt2_last) < 19:
                    inner2opt2_last = pd.to_datetime(inner2opt2_last, errors="coerce").date()
                    parsed_data['date'] = str(inner2opt2_last)
                else:
                    # Try last element of list, with deleting spaces
                    inner2opt3 = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                        .find('section', {'class': 'body-content'}) \
                        .find('div', {'class': 'innerpage2'}) \
                        .find('div', {'class': 'text'}) \
                        .find('tbody')

                    inner2opt3_last = inner2opt3.get_text().rsplit('\n')
                    inner2opt3_last = [elem for elem in inner2opt3_last if elem]  # Delete all empty strings in list
                    inner2opt3_last_emptied = inner2opt3_last[-1]

                    inner2opt3_last_emptied = pd.to_datetime(inner2opt3_last_emptied, errors="coerce").date()
                    parsed_data['date'] = str(inner2opt3_last_emptied)

            else:
                inner2opt4 = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                    .find('section', {'class': 'body-content'}) \
                    .find('div', {'class': 'innerpage2'}) \
                    .find('div', {'class': 'text'})

                # Replace because some of them has unicodedata like \xa0
                inner2opt4_last = inner2opt4.get_text().replace('\xa0', '\n').split('\n')
                # Check if the list has any empty, if yes remove them
                # Because we will need last element
                inner2opt4_last = [elem for elem in inner2opt4_last if elem]

                inner2opt4_last_emptied = inner2opt4_last[-1]
                # If asked date is not in a maximum range, it means we have wrong data
                # That is why I filter them here
                if str(pd.to_datetime(inner2opt4_last_emptied, errors="coerce")) != "NaT":
                    inner2opt4_last_emptied = pd.to_datetime(inner2opt4_last_emptied, errors="coerce", dayfirst=False)\
                                                .date()

                    parsed_data['date'] = str(inner2opt4_last_emptied)
                else:
                    inner2opt4_last_emptied = inner2opt4_last[0]
                    inner2opt4_last_emptied = pd.to_datetime(inner2opt4_last_emptied, errors="coerce", dayfirst=False)\
                                                .date()
                    if str(inner2opt4_last_emptied) == "NaT":
                        inner2optLAST = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                            .find('section', {'class': 'body-content'}) \
                            .find('div', {'class': 'innerpage2'}) \
                            .find('div', {'class': 'text'})
                        inner2optLAST_last = inner2optLAST.get_text().rsplit('\n')
                        inner2optLAST_last = [elem for elem in inner2optLAST_last if
                                              elem]  # Delete all empty strings in list
                        for truvalue in inner2optLAST_last:
                            temp = str(pd.to_datetime(truvalue, errors="coerce").date())
                            if temp != "NaT":
                                if len(temp) == 10:
                                    parsed_data['date'] = temp
                                    break
                        parsed_data['date'] = str(pd.to_datetime(inner2optLAST_last, errors="coerce").date())
                    else:
                        parsed_data['date'] = str(inner2opt4_last_emptied)

    # Extracting the content
    contentsou = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                     .find('section', {'class': 'body-content'}) \
                     .find('div', {'class': 'innerpage2'}) \
                     .find('div', {'class': 'text'})

    if contentsou is not None:
        # encode and decode for \u00e2\u20ac\u2122 strings
        parsed_data['content'] = contentsou.get_text().encode('ascii', 'ignore').decode()
    else:
        contentsou2 = soup.find('div', {'class': 'off-canvas-wrapper'}) \
                          .find('section', {'class': 'body-content'}) \
                          .find('div', {'class': 'innerpage2'}) \
                          .find('div', {'class': 'space'})
        if contentsou2 is not None:
            # encode and decode for \u00e2\u20ac\u2122 strings
            parsed_data['content'] = contentsou2.get_text().encode('ascii', 'ignore').decode()
        else:
            parsed_data['content'] = "EMPTY"

    return parsed_data


def parse_html_pages():
    # Load the parsed pages
    parsed_id_list = []
    if os.path.exists(PARSED_HTML_PATH):
        with open(PARSED_HTML_PATH, "r", encoding=ENCODING) as f:
            # Saving the parsed ids to avoid reparsing them
            for line in f:
                data = json.loads(line.strip())
                id_str = data["id"]
                parsed_id_list.append(id_str)
    else:
        with open(PARSED_HTML_PATH, "w", encoding=ENCODING) as f:
            pass

    # Iterating through html files
    for file_name in os.listdir(RAW_HTML_DIR):
        page_id = file_name[:-5]

        # Skip if already parsed
        if page_id in parsed_id_list:
            continue

        # Read the html file and extract the required information

        # Path to the html file
        file_path = os.path.join(RAW_HTML_DIR, file_name)

        try:
            parsed_data = extract_content_from_page(file_path)
            parsed_data["id"] = page_id
            print(f"Parsed page {page_id}")

            # Saving the parsed data
            with open(PARSED_HTML_PATH, "a", encoding=ENCODING) as f:
                f.write("{}\n".format(json.dumps(parsed_data)))

        except Exception as e:
            print(f"Failed to parse page {page_id}: {e}")


if __name__ == "__main__":
    parse_html_pages()
