class Lead:
    def __init__(self, title: str, email: str, website_url: str, scraped_at: str, instagram_id: str = None):
        self.title = title
        self.email = email
        self.source_url = website_url
        self.scraped_at = scraped_at
        self.instagram_id = instagram_id
        self.is_email_valid = False
        self.is_insta_valid = False
        self.is_lead_valid = False

    def to_dict(self):
        return {
            'name': self.title,
            'email': self.email,
            'source_url': self.source_url,
            'scraped_at': self.scraped_at,
            'instagram_id': self.instagram_id,
            'is_email_valid': self.is_email_valid,
            'is_insta_valid': self.is_insta_valid,
            'is_lead_valid': self.is_lead_valid
        }
