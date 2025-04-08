import time
import datetime as dt
from requests import Session
from requests.auth import HTTPBasicAuth
from .config import HOST, USER, PASSWORD


class Tiflux:
    def __init__(self, days=1):
        self.session = Session()
        self.session.auth = HTTPBasicAuth(USER, PASSWORD)
        self.last_request_time = time.time()
        self.MAX_REQUESTS_PER_MINUTE = 120
        self.URL_BASE_API = HOST
        self.days = days

    def make_request_get(self, url, params=None):
        time_since_last_request = time.time() - self.last_request_time
        necessary_wait_time = 60 / self.MAX_REQUESTS_PER_MINUTE
        if time_since_last_request < necessary_wait_time:
            wait_time = necessary_wait_time - time_since_last_request
            time.sleep(wait_time)
        response = self.session.get(url, params=params)
        self.last_request_time = time.time()

        return response.json()

    def make_request_post(self, url, data):
        time_since_last_request = time.time() - self.last_request_time
        necessary_wait_time = 60 / self.MAX_REQUESTS_PER_MINUTE
        if time_since_last_request < necessary_wait_time:
            wait_time = necessary_wait_time - time_since_last_request
            time.sleep(wait_time)
        response = self.session.post(url, json=data)
        self.last_request_time = time.time()

        return response.json()

    def make_request_put(self, url, data=None):
        time_since_last_request = time.time() - self.last_request_time
        necessary_wait_time = 60 / self.MAX_REQUESTS_PER_MINUTE
        if time_since_last_request < necessary_wait_time:
            wait_time = necessary_wait_time - time_since_last_request
            time.sleep(wait_time)
        if data:
            response = self.session.put(url, json=data)
        else:
            response = self.session.put(url)
        self.last_request_time = time.time()

        return response.json()

    def calculate_days_ago_date(self):
        current_date = dt.datetime.now()
        difference = dt.timedelta(days=self.days)
        date_ago = current_date - difference
        formatted_date = date_ago.strftime("%Y-%m-%d")
        return formatted_date

    def calculate_total_minutes(self, time_string):
        hours, minutes = map(int, time_string.split(":"))
        return hours * 60 + minutes

    def process_all_pages_and_add_to_list(self, url, params, result_list):
        params["limit"] = 200
        offset = 1
        while True:
            params["offset"] = offset
            response = self.make_request_get(url, params)
            result_list.extend(response)
            if len(response) < 200:
                break
            offset += 1

    def create_answer(self, ticket_number, name):
        url = f"{self.URL_BASE_API}tickets/{ticket_number}/answers"
        self.make_request_post(url, {"name": name})

    def create_ticket(self, data):
        url = self.URL_BASE_API + "tickets"
        response = self.make_request_post(url, data)
        ticket_number = response["ticket_number"]
        return ticket_number

    def close_ticket(self, ticket_number):
        url = f"{self.URL_BASE_API}tickets/{ticket_number}/close"
        self.make_request_put(url)

    def search_appointments(self, ticket_number):
        url = f"{self.URL_BASE_API}tickets/{ticket_number}/appointments"
        return self.make_request_get(url)

    def search_tickets(self):
        url = self.URL_BASE_API + "tickets"
        result = []
        params = {"start_date": self.calculate_days_ago_date()}
        self.process_all_pages_and_add_to_list(url, params, result)
        params["is_closed"] = "true"
        self.process_all_pages_and_add_to_list(url, params, result)
        return result

    def search_ticket(self, ticket_number):
        url = self.URL_BASE_API + "tickets/" + str(ticket_number)
        value = self.make_request_get(url)
        ticket = {
            "id": value["ticket_number"],
            "ticket_number": value["ticket_number"],
            "title": value["title"],
            "description": value["description"],
            "duration": self.calculate_total_minutes(value["worked_hours"]),
            "created_at": value["created_at"],
            "updated_at": value["updated_at"],
            "solved_in_time": value["solved_in_time"],
            "client_id": value["client"]["id"],
            "desk_id": value["desk"]["id"],
            "responsible_id": None,
            "is_closed": value["is_closed"],
        }
        if value["responsible"]:
            ticket["responsible_id"] = value["responsible"]["id"]
        return ticket

    def search_contracts(self):
        url = self.URL_BASE_API + "contracts"
        result = []
        contracts = []
        self.process_all_pages_and_add_to_list(url, {}, result)
        for contract in result:
            value = self.search_contract(contract["id"])
            if value["active"]:
                contracts.append(self.salve_contract(value))
        return contracts

    def search_contract(self, contract_id):
        url = self.URL_BASE_API + "contracts/" + str(contract_id)
        value = self.make_request_get(url)
        return value

    def salve_contract(self, value):
        contract = {
            "id": value["id"],
            "type_name": value["type_name"],
            "client_id": value["client"]["id"],
            "active": value["active"],
        }
        if value["modality"] == "Hours":
            contract["hours"] = float(
                value["contract_details"]["quantity_hours_per_cicle"].split(" ")[0]
            )
            contract["value"] = float(
                value["contract_details"]["surplus_hour_value"].split("$")[-1]
            )
        return contract
