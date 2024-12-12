import json
import pickle
from datetime import datetime, timedelta, timezone
import requests
from airflow.models import Variable
from settings.global_config import DATA_PATH, PROXIES
import logging

FILE_NAME = "cht_token.pickle"

class CHTAuth:
    """
    The class for authenticating with the CHT API.
    The class loads the password from the Airflow variables.
    The access token is saved to a file for reuse.
    """

    def __init__(self):
        self.account = Variable.get("CHT_ACCOUNT")
        self.password = Variable.get("CHT_PASSWORD")
        self.full_file_path = f"{DATA_PATH}/{FILE_NAME}"

    def get_token(self, now_time ,is_proxy=True, timeout=10):
        """
		Get the access token for authentication.
		This method retrieves the access token from the specified path.
		If the token is not found or has expired, a new token is obtained and saved to the path.

		Args:
			is_proxy (bool): Flag indicating whether to use a proxy. Defaults to True.
			timeout (int): The timeout for the request. Defaults to 10.

		Returns:
			str: The access token.

		Raises:
			FileNotFoundError: If the token file is not found.
			EOFError: If the token file is empty or corrupted.
		"""
        # Check if the token is expired
        try:
            taiwan_timezone = timezone(timedelta(hours=8))
            with open(self.full_file_path, "rb") as handle:
                res = pickle.load(handle)
                time_out = datetime.strptime(res['time_out'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=taiwan_timezone)
                if now_time < time_out:  # If the token is not expired
                    logging.info(f"time_out: {time_out}")
                    return res["access_token"]
        except (FileNotFoundError, EOFError):
            pass

        # Get the token
        url = "https://crowds.hinet.net/webapi/api/Login"
        payload = json.dumps({
            "id": self.account,
            "pass": self.password
        })
        headers = {
            'Content-Type': 'application/json'
        }
        with requests.post(
            url,
            headers=headers,
            data=payload,
            proxies=PROXIES if is_proxy else None,
            timeout=timeout,
            verify=False
        ) as response:
            res_json = response.json()    
            logging.info(f"Response JSON: {res_json}")
            token = res_json["access_token"]
            logging.info(res_json["time_out"])
            time_out = datetime.strptime(res_json["time_out"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=taiwan_timezone)
            time_out_plus_30 = time_out + timedelta(minutes=30)
            res = {"access_token": token, "time_out": time_out_plus_30}

        # Save the token
        with open(self.full_file_path, "wb") as handle:
            pickle.dump(res, handle)

        return token
