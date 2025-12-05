# Source - https://stackoverflow.com/a
# Posted by samarth mishra
# Retrieved 2025-12-05, License - CC BY-SA 4.0
import requests
from bs4 import BeautifulSoup
import datetime
import re
r=requests.get("https://skincarepakistan.com/?srsltid=AfmBOorjAUtyLBCBbFEsOw0Y_OybYBu-5CtduCUUfatmEjYEOF5W69IN")
soup=BeautifulSoup(r.text,'html.parser')
text =soup.get_text()
emails = re.findall(r'[a-z0-9]+@\S+.com', str(text))
print(emails)
