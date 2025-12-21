import re
import requests

class LeadValidator:
    """
    Handles the validation and verification of Lead attributes
    like email format and social media profile existence.
    """

    def __init__(self, validation_api_key=None):
        self.api_key = validation_api_key

    def _check_email_format(self, email: str) -> bool:
        """
        Uses a Regular Expression to check the basic syntactic format of an email.
        """
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.fullmatch(email_regex, email))

    def _verify_email_existence_api(self, email: str) -> bool:
        """
        (Placeholder) Calls a third-party API (e.g., ZeroBounce, Hunter.io)
        to check if the email address actually exists.

        NOTE: You must replace this with actual API call logic.
        For demonstration, it currently returns True.
        """
        if not self.api_key:
             return True
        return True

    def _verify_instagram_existence(self, insta_id: str) -> bool:
        """
        Checks if the Instagram profile URL is reachable (not a 404).
        It's basic and can be blocked by Instagram.
        """
        if not insta_id:
            return True

        url = f"https://www.instagram.com/{insta_id}/"
        try:
            response = requests.head(url, timeout=5)

            return response.status_code < 400
        except requests.RequestException:
            return False

    def validate_lead(self, lead_object):
        """
        Performs all validation checks and updates the Lead object's status.
        """
        is_email_valid = False
        is_insta_valid = False

        if hasattr(lead_object, 'email') and lead_object.email:
            if self._check_email_format(lead_object.email):
                is_email_valid = self._verify_email_existence_api(lead_object.email)

        if hasattr(lead_object, 'instagram_id') and lead_object.instagram_id:
            is_insta_valid = self._verify_instagram_existence(lead_object.instagram_id)

        lead_object.is_email_valid = is_email_valid
        lead_object.is_insta_valid = is_insta_valid
        lead_object.is_lead_valid = is_email_valid or is_insta_valid

        return lead_object