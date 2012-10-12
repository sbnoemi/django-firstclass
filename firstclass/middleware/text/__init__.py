from bs4 import BeautifulSoup
from .settings import FIRSTCLASS_PLAINTEXT_RULES, process_soup
import re

class PlainTextMiddleware(object):
    def process_message(self, message):
        if hasattr(message, 'attach_alternative'):
            message.attach_alternative(message.body, 'text/html')
        
        message.body = html_to_text(message.body)
        return message
        
def html_to_text(html):            
    html = re.sub('\n\n+', '\n\n', html.strip())
    soup = BeautifulSoup(html)   
    text = process_soup(soup)
    return text