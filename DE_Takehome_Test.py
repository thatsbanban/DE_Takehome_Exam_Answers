import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless") 
service = Service(r"C:\Python Projects\Basic\LEARNING_SELENIUM\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

scraped_quotes = []

driver.get("https://quotes.toscrape.com/search.aspx")
wait = WebDriverWait(driver, 15)

author_elem = wait.until(EC.presence_of_element_located((By.ID, "author")))
dropdown_author = Select(author_elem)
authors = [option.text for option in dropdown_author.options if "--" not in option.text]

for author in authors:
    print(f"Processing Author: {author}")
        
    dropdown_author = Select(driver.find_element(By.ID, "author"))
    dropdown_author.select_by_visible_text(author)
        
    wait.until(EC.presence_of_element_located((By.ID, "tag")))
    dropdown_tags = Select(driver.find_element(By.ID, "tag"))
    tags = [option.text for option in dropdown_tags.options if "--" not in option.text]


    for tag in tags:
        dropdown_tags = Select(driver.find_element(By.ID, "tag"))
        dropdown_tags.select_by_visible_text(tag)

        submit_button = driver.find_element(By.NAME, "submit_button")
        driver.execute_script("arguments[0].click();", submit_button)
    
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "content")))
        listed_quotes = driver.find_elements(By.CLASS_NAME, "quote")

        for q in listed_quotes:
            scraped_quotes.append({
                "Author": author,
                "Tag": tag,
                "Quote": q.find_element(By.CLASS_NAME, "content").text
            })

df = pd.DataFrame(scraped_quotes)
df.to_csv("all_quotes.csv", index=False, encoding="utf-8-sig")
print(f"\nDone! Save to 'all_quotes.csv'.")
driver.quit()