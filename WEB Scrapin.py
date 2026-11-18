import requests
from bs4 import BeautifulSoup
import folium

pagina = requests.get("https://roadmap.sh/")
print(pagina.status_code)