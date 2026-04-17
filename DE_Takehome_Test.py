import pandas as pd
import boto3
import os
import time
from ftplib import FTP
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

S3_BUCKET_NAME = "DE_results"
FTP_HOST = "ftp.dlptest.com"
FTP_USER = "dlpuser"
FTP_PASS = "rNrKYTX9g7z3RgJRmxWuGHbeu"
LOCAL_FILE = "all_quotes.csv"

def run_scraper():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    scraped_quotes = []

    try:
        driver.get("https://quotes.toscrape.com/search.aspx")
        wait = WebDriverWait(driver, 15)

        author_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "author"))))
        authors = [opt.text for opt in author_dropdown.options if "--" not in opt.text]

        for author in authors:
            print(f"--- Scraping: {author} ---")
            Select(driver.find_element(By.ID, "author")).select_by_visible_text(author)
            
            tag_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "tag"))))
            tags = [opt.text for opt in tag_dropdown.options if "--" not in opt.text]

            for tag in tags:
                Select(driver.find_element(By.ID, "author")).select_by_visible_text(author)
                Select(driver.find_element(By.ID, "tag")).select_by_visible_text(tag)
                
                driver.find_element(By.NAME, "submit_button").click()
                time.sleep(0.5) 

                quotes = driver.find_elements(By.CLASS_NAME, "quote")
                for q in quotes:
                    scraped_quotes.append({
                        "Author": author,
                        "Tag": tag,
                        "Quote": q.find_element(By.CLASS_NAME, "content").text
                    })

        df = pd.DataFrame(scraped_quotes)
        df.to_csv(LOCAL_FILE, index=False, encoding="utf-8-sig")
        print(f"Done! Found {len(df)} total quotes.")
        return True

    except Exception as e:
        print(f"Scraper error: {e}")
        return False
    finally:
        driver.quit()

def upload_to_s3():
    try:
        print("Uploading to S3...")
        s3 = boto3.client('s3')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        s3_key = f"scraped_data/{timestamp}_{LOCAL_FILE}"
        s3.upload_file(LOCAL_FILE, S3_BUCKET_NAME, s3_key)
        print(f"S3 Success: {s3_key}")
    except Exception as e:
        print(f"S3 Error: {e}")

def upload_to_ftp():
    try:
        print("Uploading to FTP...")
        with FTP(FTP_HOST) as ftp:
            ftp.login(user=FTP_USER, passwd=FTP_PASS)
            with open(LOCAL_FILE, 'rb') as f:
                ftp.storbinary(f"STOR {LOCAL_FILE}", f)
        print("FTP Success.")
    except Exception as e:
        print(f"FTP Error: {e}")

if __name__ == "__main__":
    if run_scraper():
        upload_to_s3()
        upload_to_ftp()
        if os.path.exists(LOCAL_FILE):
            os.remove(LOCAL_FILE)