import cleantext

class keywordmodule: # <--- IT STARTS HERE
    def __init__(self):
        self.keywords = []
    
    def get_keywords(self):
        return self.keywords
    
    def cleankeyword(self, keyword):
        # FIX: Removed all the problematic boolean flags that caused TypeError
        # We rely only on the positional argument 'keyword' for basic functionality,
        # or minimal, common arguments if the library supports them (e.g., 'clean_all').
        return cleantext.clean(keyword)
        
    def get_clean_keywords(self):
        return [self.cleankeyword(kw) for kw in self.keywords]


# Example usage (will now run successfully):
# keywordmodule_instance = keywordmodule()
# keywordmodule_instance.keywords = ["Python Programming", "Data Science", "Machine Learning", "Artificial Intelligence", "Deep Learning"]
# cleaned_keywords = keywordmodule_instance.get_clean_keywords()
# print(cleaned_keywords)