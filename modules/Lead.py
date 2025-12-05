class Lead:
    def __init__(self, title: str, email: str, website_url: str, scraped_at: str):
        self.title = title
        self.email = email
        self.source_url = website_url
        self.scraped_at = scraped_at

    def to_dict(self):
        return {
            'name': self.title,
            'email': self.email,
            'source_url': self.source_url,
            'scraped_at': self.scraped_at
        }
