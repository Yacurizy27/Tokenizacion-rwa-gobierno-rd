from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

driver.get("https://roadmap.sh/devops")

time.sleep(5)

contenido = driver.find_element(By.TAG_NAME, "body").text

with open("devops.txt", "w", encoding="utf-8") as archivo:
    archivo.write(contenido)

driver.quit()

print("Contenido exportado a devops.txt")


