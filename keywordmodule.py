import cleantext
class keywordmodule: # <--- IT STARTS HERE
    def __init__(self):
        self.keywords = []
    def get_keywords(self):
        return self.keywords
    def cleankeyword(self,keyword):
        return cleantext.clean(keyword, no_line_breaks=True, lower=True, no_urls=True, no_emails=True, no_phone_numbers=True
        )
    def get_clean_keywords(self):
        return [self.cleankeyword(kw) for kw in self.keywords]


    
       

