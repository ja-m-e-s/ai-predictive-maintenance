import random, requests, time

random.seed()
url = "http://192.168.0.2"

while True:    
    secs = random.uniform(0, 30)
    print(f"Sleeping for {secs} seconds...")
    time.sleep(secs)
    print(f"Sending GET request to {url}")
    r = requests.get(url)
    print(f"Request status code: {r.status_code}")
    
    

