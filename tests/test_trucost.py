import requests
from bs4 import BeautifulSoup

URL = "https://trucost.cloud/instances/ec2/ap-south-1/t3.micro"

response = requests.get(URL, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

print("Page downloaded successfully.")
print("Status code:", response.status_code)

print("\n===== TABLES FOUND =====")

tables = soup.find_all("table")

print("Number of tables:", len(tables))

for i, table in enumerate(tables, start=1):

    rows = table.find_all("tr")

    print("\n----------------------------------------")
    print("TABLE", i)
    print("Rows:", len(rows))
    print("----------------------------------------")

    for row in rows[:10]:

        cells = row.find_all(["th", "td"])

        values = [
            cell.get_text(" ", strip=True)
            for cell in cells
        ]

        print(values)