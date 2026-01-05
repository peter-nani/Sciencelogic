import requests
import urllib3

# Disables the 'InsecureRequestWarning' for the internal IP
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Define the endpoint and credentials
url = "https://192.168.1.2/gql"
auth = ('', '') # Replace with your SL1 credentials

# 2. Define the GraphQL query
# Note: Using the variable pattern we discussed
query = """
query MyQuery($company_filter: TextSearch) {
  events(search: { organization: { has: { company: $company_filter } } }) {
    edges {
      node {
        id
        organization {
          id
          company
          email
        }
      }
    }
  }
}
"""

# 3. Define the variables
variables = {
    "company_filter": {
        "eq": "kennerabank"
    }
}

# 4. Execute the request
response = requests.post(
    url,
    json={'query': query, 'variables': variables},
    auth=auth,
    verify=False  # Set to False because of the "Not secure" local IP
)

# 5. Handle the output
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Query failed with status code {response.status_code}: {response.text}")