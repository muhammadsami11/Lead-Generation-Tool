import unittest
from modules.leadExtractor import LeadExtractor

class TestLeadExtractor(unittest.TestCase):
    """Tests all helper functions within the LeadExtractor class."""

    def setUp(self):
        """Set up the LeadExtractor object before each test run."""
        # Initialize the class you want to test
        self.extractor = LeadExtractor()

    def test_clean_url_normalization(self):
        """
        Tests if URLs are correctly cleaned by removing paths, parameters, 
        and fragments, and normalizing the protocol.
        """
        # --- 1. Define Test Data (Input) ---
        messy_urls = [
            "https://www.example.com/product/123?ref=ad#details", # Messy
            "http://blog.sample.net/page/",                      # HTTP, trailing slash
            "https://www.google.com/search?q=test&ie=UTF-8",     # Search query
            "https://app.mysite.com"                             # Clean already
        ]

        # --- 2. Define Expected Output ---
        expected_urls = [
            "https://www.example.com",
            "http://blog.sample.net",
            "https://www.google.com",
            "https://app.mysite.com"
        ]

        # --- 3. Run the Function and Assert ---
        actual_urls = self.extractor.clean_url(messy_urls)
        
        # We assert that the list we got matches the list we expected
        self.assertEqual(actual_urls, expected_urls, 
                         "The clean_url function did not normalize the URLs correctly.")

    def test_clean_url_empty_list(self):
        """Tests handling an empty input list."""
        self.assertEqual(self.extractor.clean_url([]), [], 
                         "Should return an empty list when given an empty list.")

if __name__ == '__main__':
    unittest.main()