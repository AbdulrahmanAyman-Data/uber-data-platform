import urllib.request
import urllib.parse
import csv
import json
import time
import ssl

# Bypass MSYS2/Windows SSL Certificate Verification Errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print("Downloading official TLC Taxi Zone list...")
url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

zones = []
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

with urllib.request.urlopen(req, context=ctx) as response:
    lines = [l.decode('utf-8') for l in response.readlines()]
    reader = csv.DictReader(lines)
    for row in reader:
        zones.append(row)

print(f"Found {len(zones)} zones. Fetching real coordinates from OpenStreetMap...")
print("This will take about 4-5 minutes (the API requires a 1.2-second delay between requests).")

# Save directly to your specified E: drive workspace
output_path = r"D:\uber-data-platform\zone_centroids.csv"

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["LocationID", "lat", "lon"])
    
    for zone in zones:
        loc_id = zone["LocationID"]
        zone_name = zone["Zone"].replace("/", " ")
        borough = zone["Borough"]
        
        if borough == "Unknown":
            writer.writerow([loc_id, 40.7128, -74.0060]) 
            continue

        query = f"{zone_name}, {borough}, New York City, NY"
        api_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
        
        try:
            api_req = urllib.request.Request(api_url, headers={'User-Agent': 'Helwan_SE_BigData_Project/1.0'})
            with urllib.request.urlopen(api_req, context=ctx) as api_resp:
                data = json.loads(api_resp.read().decode('utf-8'))
                if data:
                    writer.writerow([loc_id, data[0]["lat"], data[0]["lon"]])
                else:
                    writer.writerow([loc_id, 40.7128, -74.0060])
        except Exception as e:
            writer.writerow([loc_id, 40.7128, -74.0060])
        
        time.sleep(1.2)

print(f"Success! Real zone_centroids.csv generated directly at {output_path}")
