import requests
import re
import csv
from time import sleep

with open("cookie.txt", "r") as file:
    cookies = file.read().strip()
s = requests.Session()


class LinkedIn:
    def __init__(self, output_file_name="employee_new.csv"):
        self.fieldnames = [
            "Company Name",
            "Domain",
            "Profile Link",
            "Name",
            "Designation",
            "Location",
        ]
        self.output_file_name = output_file_name
        self.session = requests.Session()
        self.cookies = self.load_cookies_from_file("cookie.txt")

    def load_cookies_from_file(self, filepath):
        with open(filepath, "r") as file:
            cookies = file.read().strip()
        return cookies

    def save_data(self, dataset):
        with open(
            self.output_file_name, mode="a+", encoding="utf-8-sig", newline=""
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=self.fieldnames, delimiter=",", quotechar='"'
            )
            if csv_file.tell() == 0:
                writer.writeheader()
            writer.writerow(
                {
                    "Company Name": dataset[0],
                    "Domain": dataset[1],
                    "Profile Link": dataset[2],
                    "Name": dataset[3],
                    "Designation": dataset[4],
                    "Location": dataset[5],
                }
            )

    @staticmethod
    def get_company_id(company_link):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Dnt": "1",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }

        try:
            response = requests.get(company_link, headers=headers)
            response.raise_for_status()  # will throw an error for bad status
            company_id = re.findall(
                r'"objectUrn":"urn:li:organization:([\d]+)"', response.text
            )[0]
            return company_id
        except requests.RequestException as e:
            print(f"Failed to get company ID: {str(e)}")
            return None

    def paginate_results(self, company_id, company_name, domain):
        headers = {
            "Accept": "application/vnd.linkedin.normalized+json+2.1",
            "Cookie": cookies,
            "Csrf-Token": re.findall(r'JSESSIONID="(.+?)"', cookies)[0],
            "Dnt": "1",
            "Referer": "https://www.linkedin.com/search/results/people/?currentCompany=%5B%22"
            + company_id
            + "%22%5D&origin=COMPANY_PAGE_CANNED_SEARCH&page=2&sid=7Gd",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "X-Li-Lang": "en_US",
            "X-Li-Page-Instance": "urn:li:page:d_flagship3_search_srp_people_load_more;Ux/gXNk8TtujmdQaaFmrPA==",
            "X-Li-Track": '{"clientVersion":"1.13.9792","mpVersion":"1.13.9792","osName":"web","timezoneOffset":6,"timezone":"Asia/Dhaka","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":1.3125,"displayWidth":1920.1875,"displayHeight":1080.1875}',
            "X-Restli-Protocol-Version": "2.0.0",
        }
        page_no = 0
        print("Starting pagination for company:", company_name)

        for page_no in range(0, 1):
            print("Checking facet: {}/3".format(page_no))
            link = (
                "https://www.linkedin.com/voyager/api/graphql?variables=(start:"
                + str(page_no)
                + ",origin:COMPANY_PAGE_CANNED_SEARCH,query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List("
                + company_id
                + ")),(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false))&queryId=voyagerSearchDashClusters.e1f36c1a2618e5bb527c57bf0c7ebe9f"
            )

            try:
                resp = s.get(link, headers=headers).json()
            except:
                print("Failed to open {}".format(link))
                continue
            results = resp.get("included")
            for person_data in results:
                if (
                    person_data.get("$type")
                    == "com.linkedin.voyager.dash.search.EntityResultViewModel"
                ):
                    company_name = company_name
                    person_name = person_data.get("title").get("text")
                    profile_link = person_data.get("navigationUrl")
                    designation = person_data.get("primarySubtitle").get("text")
                    person_location = person_data.get("secondarySubtitle").get("text")
                    print("Company: " + company_name)
                    print("Profile Link: {}".format(profile_link))
                    print("Name: {}".format(person_name))
                    print("Designation: {}".format(designation))
                    print("Location: {}".format(person_location))
                    print()
                    dataset = [
                        company_name,
                        domain,
                        profile_link,
                        person_name,
                        designation,
                        person_location,
                    ]
                    if person_name != "" and person_name != "LinkedIn Member":
                        self.save_data(dataset)
            sleep(3)
