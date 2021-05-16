# -*- coding: utf-8 -*-
# !/usr/bin/env python
# Columbus - Personalised Travel Itineraries based on experience, country or preferred destination.
# Contact Milind Deore <tomdeore@gmail.com>
#

import time
import re
import csv
import os
import logging
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException


class GoogleDestination:
    def __init__(self, country):
        self.country = country
        self.destinations = {}
        self.url = 'https://www.google.com/destination'
        self.driver = ''
        self.current_destination = ''


    def open_browser(self):
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(chrome_options = options)


    def search(self):
        """
            Find the search input element and enter the country name.
        """
        try:
            self.driver.get(self.url)
            # wait to loading of search input element
            search_input_present = EC.visibility_of_element_located((By.XPATH, "//div[@class='gb_Xe']//input"))
            WebDriverWait(self.driver, 20).until(search_input_present)
            input_elem = self.driver.find_element(By.XPATH, "//div[@class='gb_Xe']//input")
            input_elem.click()
            time.sleep(1) # guarantee
            input_elem.send_keys(self.country, Keys.ARROW_DOWN) # write country end select first result
            time.sleep(1)
            # wait to loading of search results menu
            search_results_present = EC.visibility_of_element_located((By.XPATH, "//ul[@class='sbsb_b']"))
            WebDriverWait(self.driver, 20).until(search_results_present)
            time.sleep(1) # guarantee
            input_elem.send_keys(Keys.ENTER)
            destination_page_present = EC.visibility_of_element_located((By.XPATH, "//div[@class='RrdlOe']"))
            WebDriverWait(self.driver, 20).until(destination_page_present)
            return True
        except TimeoutException:
            print("1. Timeout problem please try again.")
            return False
        except Exception as e:
            print(e)
            return False


    def get_destinations(self, at=0):
        """
            Get urls of destinations according to each option and append to list.
        """
        attempt = at
        try:
            # wait to be clickable of destinations link
            destinations_elem_present = EC.element_to_be_clickable((By.XPATH, "//li[@id='DESTINATIONS']"))
            WebDriverWait(self.driver, 20).until(destinations_elem_present)
            destinations_elem = self.driver.find_element(By.XPATH, "//li[@id='DESTINATIONS']").find_element_by_tag_name('a').click() # click destinations link
            # wait to loading of destinations list
            destinations_list_present = EC.visibility_of_element_located((By.XPATH, "//div[@class='BvC61c RrdlOe']"))
            WebDriverWait(self.driver, 20).until(destinations_list_present)
            # maybe if block for are there any option?
            options = self.driver.find_element_by_xpath("//span[@class='irTQQe']").find_elements_by_tag_name("chip-button")
            if len(options) == 0:
                destination_lists = self.driver.find_elements_by_xpath("//a[@class='sjglme']")
                for destination in destination_lists:
                    destination_name = destination.find_element_by_tag_name("h2").get_attribute('innerHTML')
                    if destination_name not in self.destinations:
                        destination_url = destination.get_attribute('href')
                        self.destinations[destination_name] = {}
                        self.destinations[destination_name]['URL'] = destination_url
                        self.destinations[destination_name]['Options'] = None
                return True
            else:
                for i in range(len(options)):
                    temp_class_of_content = self.driver.find_element_by_xpath("//div[contains(@class,'LOIWPe')]").get_attribute("class")
                    self.driver.find_element_by_xpath("//span[@class='irTQQe']").find_elements_by_tag_name("chip-button")[i].click()
                    time.sleep(1)
                    # wait until to changing of content
                    while True:
                        current_class_of_content = self.driver.find_element_by_xpath("//div[contains(@class,'LOIWPe')]").get_attribute("class")
                        if current_class_of_content == temp_class_of_content:
                            time.sleep(3)
                        else:
                            break
                    option_name = self.driver.find_element_by_xpath("//chip-button[@aria-checked='true']").find_element_by_class_name("gws-travel-controls__chip-label").get_attribute("innerHTML")
                    # get destinations on selected option
                    destination_lists = self.driver.find_elements_by_xpath("//a[@class='sjglme']")
                    for destination in destination_lists:
                        destination_name = destination.find_element_by_tag_name("h2").get_attribute('innerHTML')
                        if destination_name not in self.destinations:
                            destination_url = destination.get_attribute('href')
                            self.destinations[destination_name] = {}
                            self.destinations[destination_name]['URL'] = destination_url
                            self.destinations[destination_name]['Options'] = []
                        self.destinations[destination_name]['Options'].append(option_name)
                    self.driver.find_element_by_xpath("//span[@class='irTQQe']").find_elements_by_tag_name("chip-button")[i].click()
                    time.sleep(1)
                    # wait until to changing of content
                    while True:
                        temp_class_of_content = self.driver.find_element_by_xpath("//div[contains(@class,'LOIWPe')]").get_attribute("class")
                        if current_class_of_content == temp_class_of_content:
                            time.sleep(3)
                        else:
                            break
                return True
        except StaleElementReferenceException:
            # if stale exception occur, try again three times
            if attempt == 4:
                return False
            attempt += 1
            return self.get_destinations(attempt)
        except TimeoutException:
            print("2. Timeout problem please try again.")
            return False
        except Exception as e:
            print(e)
            return False


    def get_destination_details(self, url, at=0):
        attempt = at
        try:
            self.driver.get(url)
            destination_detail_present = EC.visibility_of_element_located((By.XPATH, "//div[@class='AofZnb']"))
            WebDriverWait(self.driver, 20).until(destination_detail_present)
        except TimeoutException:
            if attempt == 3:
                print("Problem with destination ", url)
                return False
            attempt += 1
            return self.get_destination_details(url, attempt)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        destination = soup.find('div', class_='AofZnb').text # destination name
        self.current_destination = destination
        months = {}
        month_table = soup.find_all('table', class_='qt3FE')
        if len(month_table) > 1:
            months['Country'] = self.country
            months['Destination'] = self.current_destination
            months['Months'] =  {}
            tr = month_table[1].find_all('tr')
            for row in tr[1:13]:
                month_name = row.find('td').text
                other_elems = row.find_all('td', class_='qRa1yd')
                months['Months'][month_name] = {}
                months['Months'][month_name]['Popularity'] = ''
                months['Months'][month_name]['MinTemp'] = ''
                months['Months'][month_name]['MaxTemp'] = ''
                months['Months'][month_name]['Precipitation'] = ''
                for elem in other_elems:
                    length_of_spans = len(elem.find_all('span'))
                    # popularity
                    if length_of_spans == 1:
                        popularity = elem.find('span')
                        if popularity.has_attr('aria-label'):
                            popularity = elem.find('span')['aria-label']
                            popularity = re.findall(r'\d+\.\d+|\d+', popularity)[0]
                            months['Months'][month_name]['Popularity'] = popularity
                    # tempature
                    if length_of_spans == 2:
                        tempatures = [i.text for i in elem.find_all('span')]
                        months['Months'][month_name]['MaxTemp'] = tempatures[0]
                        months['Months'][month_name]['MinTemp'] = tempatures[1].split("/")[1]
                    # precipitation
                    if length_of_spans == 0:
                        precipitation = elem.text
                        months['Months'][month_name]['Precipitation'] = precipitation
            return months
        else:
            return False


    def get_topsgihts_details(self, at=0):
        attempt = at
        try:
            # click the top sight element on menu
            self.driver.find_element(By.XPATH, "//li[@id='TOP_SIGHTS']").find_element_by_tag_name('a').click()
            # wait to loading of top sight page of destination
            top_sights_list_present = EC.visibility_of_element_located((By.XPATH, "//div[@class='w9GWWb']"))
            WebDriverWait(self.driver, 20).until(top_sights_list_present)
            top_sights = self.driver.find_element_by_tag_name('ol').find_elements_by_tag_name('li') # get all topsight element on destination
            top_sights_detail = {}
            top_sights_detail['Country'] = self.country
            top_sights_detail['Destination'] = self.current_destination
            top_sights_detail['Topsights'] = {}
            for idx,top_sight in enumerate(top_sights):
                top_sight.click() # click each top sight item by one by
                try:
                    # wait to loading of the content of top sight
                    top_sight_present = EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'au3Yqc')]"))
                    WebDriverWait(self.driver, 20).until(top_sight_present)
                except TimeoutException:
                    continue
                top_sight_html = top_sight.get_attribute('innerHTML')
                # get details
                soup = BeautifulSoup(top_sight_html, 'html.parser')
                place_name = soup.find('h2', class_='NbdpWc').text
                # rating
                rating = soup.find('span', class_='rtng')
                if rating:
                    if len(rating) == 2:
                        rating.style.decompose()
                    rating = rating.text
                else:
                    rating = ''
                # number of reviews
                number_of_reviews = soup.find('span', attrs={'class':'Vfp4xe p13zmc'})
                if number_of_reviews:
                    if len(number_of_reviews) == 2:
                        number_of_reviews.style.decompose()
                    number_of_reviews = number_of_reviews.text.strip()
                else:
                    number_of_reviews = ''
                # get the details of typical time spent
                if self.driver.find_element_by_tag_name('async-local-kp').is_displayed() == True:
                    time_spent_html = self.driver.find_element_by_tag_name('async-local-kp').get_attribute('innerHTML')
                else:
                    time_spent_html = self.driver.find_element_by_id('gws-trips-desktop__dest-mrgkp').get_attribute('innerHTML')
                time_spent_soup = BeautifulSoup(time_spent_html,'html.parser')
                time_spent = time_spent_soup.find('div', class_='UYKlhc')
                if time_spent:
                    time_spent = time_spent.find('b').text
                else:
                    time_spent = ''
                # add details to dict
                top_sights_detail['Topsights'][idx] = {}
                top_sights_detail['Topsights'][idx]['Place Name'] = place_name
                top_sights_detail['Topsights'][idx]['Rating'] = rating
                top_sights_detail['Topsights'][idx]['Number of Reviews'] = number_of_reviews
                top_sights_detail['Topsights'][idx]['Typical Time Spent'] = time_spent
                # wait to close element
                close_present = EC.element_to_be_clickable((By.TAG_NAME, "g-fab"))
                WebDriverWait(self.driver, 20).until(close_present)
                self.driver.find_element_by_tag_name('g-fab').click()
                time.sleep(1)
            return top_sights_detail
        except NoSuchElementException:
            # if there are no topsight at 'destination'
            return False
        except Exception as e:
            if attempt == 2:
                print(e, " .3.")
                return False
            attempt += 1
            return self.get_topsgihts_details(attempt)


    def write_month(self, data):
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + '/Months.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            file_is_empty = os.stat(path + '/Months.csv').st_size == 0
            if file_is_empty:
                fields = ['Country', 'Destination', 'Month', 'Popularity', 'MinTemp', 'MaxTemp', 'Precipitation']
                writer.writerow(fields)
            #
            for key, items in data['Months'].items():
                writer.writerow([data['Country'],
                                 data['Destination'],
                                 key,
                                 items['Popularity'],
                                 items['MinTemp'],
                                 items['MaxTemp'],
                                 items['Precipitation']])


    def write_top_sight(self, data):
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + '/ThingsToDo.csv', 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            option_fields = {'Architecture': 0, 'Nature': 1, 'Shopping': 2, 'Fishing': 3, 'Hiking': 4, 'Outdoor Recreation': 5, 'Adventure': 6,
                             'Beaches': 7, 'Camping': 8, 'Caves': 9, 'Museums': 10, 'National Parks': 11, 'Art': 12, 'Desert': 13, 'Coral reef': 14, 'Skiing': 15,
                             'Snowboarding': 16, 'Winter sports': 17, 'Wildlife': 18, 'Penguin': 19, 'Glacier': 20, 'Ecotourism': 21, 'Snorkeling': 22, 'Koala': 23,
                             'Surfing': 24, 'Nature reserve': 25, 'Volcano': 26, 'Sailing': 27, 'Scuba diving': 28, 'Theaters': 29, 'Elephant': 30, 'Safari': 31,
                             'Jaguar': 32, 'Casinos': 33, 'Kitesurfing': 34, 'Windsurfing': 35, 'Birdwatching': 36, 'Rainforest': 37, 'Nightlife': 38,
                             'Whale watching': 39, 'Reindeer': 40, 'Gorilla': 41, 'Kayaking': 42, 'Polar bear': 43, 'Hot spring': 44, 'Tiger': 45, 'Yoga': 46,
                             'Orangutan': 47, 'Golf': 48, 'Rafting': 49, 'Autumn leaf color': 50, 'Dolphin': 51, 'Wine tasting': 52, 'Climbing': 53, 'Paragliding': 54,
                             'Bungee jumping': 55, 'Whale shark': 56, 'Alpine skiing': 57, 'Historic site': 58}
            file_is_empty = os.stat(path + '/ThingsToDo.csv').st_size == 0
            if file_is_empty:
                fields = ['Country', 'Destination', 'Things to Do', 'Rating', 'Number of Review', 'Typical Time Spent']
                fields.extend([key for key in option_fields])
                writer.writerow(fields)
            # write options
            options = ['no' for key in option_fields]
            destination = data['Destination']
            if self.destinations[destination]['Options'] != None:
                for o in self.destinations[destination]['Options']:
                    idx = option_fields.get(o)
                    if idx != None:
                        options[idx] = 'yes'
            # write data
            for key, items in data['Topsights'].items():
                row = [data['Country'],
                       data['Destination'],
                       items['Place Name'],
                       items['Rating'],
                       items['Number of Reviews'],
                       items['Typical Time Spent']]
                row += options
                writer.writerow(row)


    def run(self):
        self.open_browser()
        search = self.search()
        if search == True:
            get_dests = self.get_destinations()
            if get_dests == True:
                counter = 0
                for key, item in self.destinations.items():
                    if counter % 20 == 0:
                        # re open browser for memory
                        self.driver.close()
                        self.open_browser()
                    counter += 1
                    print('{}/{}'.format(counter, len(self.destinations)))
                    dest_details = self.get_destination_details(item['URL'])
                    if dest_details != False:
                        self.write_month(dest_details)
                    topsight_details = self.get_topsgihts_details()
                    if topsight_details != False:
                        self.write_top_sight(topsight_details)


country = input("Enter Country: ")
a = GoogleDestination(country)
a.run()
