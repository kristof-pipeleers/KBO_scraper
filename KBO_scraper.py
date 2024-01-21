from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import requests
import tabula
from typing import List
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException

load_dotenv()
login = True

def choose_location(locations):
    print(f"There are multiple locations for the specified location:")
    for i, loc in enumerate(locations, start=1):
        print(f"{i}: {loc}")

    while True:
        try:
            choice = int(input("Enter the number corresponding to the correct location: "))
            if 1 <= choice <= len(locations):
                return locations[choice - 1]
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def check_value_on_page(driver, value):
    try:
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.XPATH, f'//*[contains(text(), "{value}")]'), value)
        )
        return True
    except TimeoutException:
        return False
    
def next_page_exists(driver):
    try:
        driver.find_element(By.LINK_TEXT, "Volgende")
        return True
    except NoSuchElementException:
        return False
    

def get_employee_count(ondernemingsnummer, driver):
    global login
    try:
        if login:
            driver.get("https://bizzy.org/nl")
            login = False

            accept_cookies_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.styles_button__ljEg8.styles_accept__dqSGH"))
            )
            accept_cookies_button.click()

            start_button = driver.find_element(By.CSS_SELECTOR, "button.styles_button__2Udr_.styles_buttonLarge__1sqdg.styles_buttonMin__jXUkl.styles_buttonFilled__xZ02u.styles_buttonPurple__Psh12")
            start_button.click()

            checkbox_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='checkbox'].styles_input__slqQ3"))
            )
            if not checkbox_element.is_selected():
                checkbox_element.click()

            google_sign_in_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "styles_signInGoogle__QfQjP"))
            )
            google_sign_in_element.click()

            # Wacht tot het nieuwe venster/tabblad geladen is
            WebDriverWait(driver, 10).until(lambda driver: len(driver.window_handles) > 1)

            # Schakel over naar het nieuwe venster/tabblad
            new_window = driver.window_handles[1]
            driver.switch_to.window(new_window)

            # Voer acties uit in het nieuwe venster/tabblad
            email_input_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input_element.send_keys(os.getenv("GOOGLE_EMAIL"))

            # Wacht tot de 'Volgende' knop aanwezig is en klik erop
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div#identifierNext button.VfPpkd-LgbsSe"))
            )
            driver.execute_script("arguments[0].click();", next_button)

            password_input_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'].whsOnd.zHQkBf"))
            )
            password_input_element.send_keys(os.getenv("GOOGLE_PASSWORD"))

            # Wacht tot de 'Volgende' knop na wachtwoordinvoer zichtbaar en klikbaar is
            next_button_after_password = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "passwordNext"))
            )
            driver.execute_script("arguments[0].click();", next_button_after_password)
                
            original_window = driver.window_handles[0]
            driver.switch_to.window(original_window)

        ondernemingsnummer_short = ondernemingsnummer.replace('.', '')
        driver.get(f"https://bizzy.org/nl/be/{ondernemingsnummer_short}")
        print(f"https://bizzy.org/nl/be/{ondernemingsnummer_short}")
        werknemersaantal, omzet = extract_company_data(driver)
        return werknemersaantal, omzet

    except Exception as e:
        print(f"Kon het werknemersaantal of omzet niet vinden voor ondernemingsnummer: {ondernemingsnummer}. Fout: {e}")
        return None, None

def extract_company_data(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    werknemers_aantal = extract_detail(soup, 'Werknemers (aantal)', 'Geschat aantal werknemers')
    omzet = extract_detail(soup, 'Geschatte omzet', 'Omzet')

    return werknemers_aantal, omzet

def extract_detail(soup, *search_terms):
    for term in search_terms:
        element = soup.find('span', class_='styles_title__I5uU8', string=lambda text: term in text)
        if element:
            return element.find_next_sibling('div', class_='styles_value__SIMU3').find('span', class_='styles_number__8SAss').text
    print(f"Elementen voor {' of '.join(search_terms)} niet gevonden")
    return None

def scrape_data(nace_code, location, temp_pdf_filename, option, csv_file, driver):

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'nacecodes')))

        nace_input = driver.find_element(By.ID, 'nacecodes')
        match option:
            case 1:
                municipality_selector = ('gem', 'gemeente1')
            case 2:
                municipality_selector = ('gemb', 'gemeente0')
            case 3:
                municipality_selector = ('post', 'postnummer1')

        municipality_radio, municipality_input = [driver.find_element(By.ID, id) for id in municipality_selector]
        search_button = driver.find_element(By.NAME, 'actionLu')

        nace_input.send_keys(nace_code)
        municipality_radio.click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, municipality_input.get_attribute('id'))))
        municipality_input.send_keys(location)

        handle_location_input(driver, option, municipality_input)

        search_button.click()
        pdf_url = driver.find_element(By.XPATH, '//a[contains(@href, "activiteitenlijst.pdf")]').get_attribute('href')
        download_pdf(pdf_url, temp_pdf_filename)

        ondernemingsnummers = extract_ondernemingsnummers(driver, nace_code)
        process_pdf(temp_pdf_filename, ondernemingsnummers, nace_code, csv_file)

    except TimeoutException:
        print(f"No results found for location: {location} or NACE-code is incorrect.")
    finally:
        driver.quit()

def handle_location_input(driver, option, municipality_input):
    if option != 3:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.autocomplete ul li.selected')))
        location_options = driver.find_elements(By.CSS_SELECTOR, '.autocomplete ul li')
        if len(location_options) > 1:
            selected_location = choose_location([option.text for option in location_options])
            municipality_input.clear()
            municipality_input.send_keys(selected_location)

def download_pdf(pdf_url, filename):
    response = requests.get(pdf_url)
    with open(filename, 'wb') as file:
        file.write(response.content)
        
def extract_ondernemingsnummers(driver, nace_code):
    ondernemingsnummers_with_urls = []
    while True:
        rows = driver.find_elements(By.XPATH, '//tbody/tr')
        for row in rows:
            ondernemingsnummer_element = row.find_element(By.XPATH, './td[3]/a')
            ondernemingsnummer = ondernemingsnummer_element.text.strip()
            ondernemingsnummer_url = ondernemingsnummer_element.get_attribute('href')
            ondernemingsnummers_with_urls.append((ondernemingsnummer, ondernemingsnummer_url))

        if not next_page_exists(driver):
            break

        driver.find_element(By.LINK_TEXT, "Volgende").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//tbody/tr')))

    ondernemingsnummers = []
    for ondernemingsnummer, ondernemingsnummer_url in ondernemingsnummers_with_urls:

        driver.get(ondernemingsnummer_url)
        nace_code_present = False
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//a[contains(@href, "naceToelichting.html?nace.code={nace_code}")]')))
            nace_code_present = True
        except TimeoutException:
            print(f"Desired information not found for ondernemingsnummer: {ondernemingsnummer}")

        if nace_code_present:
            werknemersaantal, omzet = get_employee_count(ondernemingsnummer, driver)
            ondernemingsnummers.append((ondernemingsnummer, werknemersaantal, omzet))
    print("Ondernemingsnummers with the desired nace code:", ondernemingsnummers)

    return ondernemingsnummers

def process_pdf(pdf_filename, ondernemingsnummers, nace_code, csv_file):
    tables = tabula.read_pdf(pdf_filename, pages="all", lattice=True, pandas_options={'header': None})
    ondernemingsnummers_dict = {num: (werknemersaantal, omzet) for num, werknemersaantal, omzet in ondernemingsnummers}
    for df in tables[1:]:
        df = prepare_dataframe(df, ondernemingsnummers_dict, nace_code)
        df.to_csv(csv_file, mode='a', header=False, index=False)

def prepare_dataframe(df, ondernemingsnummers_dict, nace_code):
    df_copy = df.copy()
    df_copy.replace(to_replace=[r'\r', r'\n'], value=' ', regex=True, inplace=True)
    df_copy = df_copy.iloc[1:-1]
    df_copy['Nace code'] = nace_code
    df_copy = df_copy[df_copy.iloc[:, 1].isin(ondernemingsnummers_dict.keys())]
    df_copy['Werknemersaantal'] = df_copy.iloc[:, 1].apply(lambda num: ondernemingsnummers_dict[num][0] if num in ondernemingsnummers_dict else None)
    df_copy['Omzet'] = df_copy.iloc[:, 1].apply(lambda num: ondernemingsnummers_dict[num][1] if num in ondernemingsnummers_dict else None)
    return df_copy

def kbo_scraper(locations: List[str], nace_codes: List[str], option: int):

    csv_file = 'output.csv'
    clear_file(csv_file)

    for location in locations:
        for nace_code in nace_codes:
            process_nace_location_pair(nace_code, location, option, csv_file)

def print_usage_and_exit():
    print("Usage: python KBO_scraper.py <arg1> <arg2> <arg3>")
    print("1: search for 'gemeente'")
    print("2: search for 'gemeente & buurgemeenten'")
    print("3: search for 'postcode'")
    print("<arg2>: path of the NACE code text file")
    print("<arg3>: path of the location text file")
    sys.exit(1)

def read_lines_from_file(filepath):
    with open(filepath, 'r') as file:
        return file.read().splitlines()

def clear_file(filepath):
    with open(filepath, 'w') as file:
        pass

def process_nace_location_pair(nace_code, location, option, csv_file):
    driver = setup_chrome_driver()
    try:
        temp_pdf_filename = create_temp_pdf_filename()
        scrape_data(nace_code, location, temp_pdf_filename, option, csv_file, driver)
        print(f"nace code: {nace_code} for location: {location} is visible in csv file.")
    finally:
        cleanup_resources(temp_pdf_filename, driver)

def setup_chrome_driver():
    chrome_options = uc.ChromeOptions()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option(
        "prefs", {
            # block image loading
            "profile.managed_default_content_settings.images": 2,
        }
    )
    chrome_options.add_argument("https://kbopub.economie.fgov.be/kbopub/zoekactiviteitform.html")
    driver = uc.Chrome(options=chrome_options)
    driver.delete_all_cookies()
    return driver

def create_temp_pdf_filename():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f'temp_{timestamp}.pdf'

def cleanup_resources(temp_pdf_filename, driver):
    os.remove(temp_pdf_filename)
    driver.quit()
