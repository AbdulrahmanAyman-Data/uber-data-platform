import csv

# Generate baseline NYC coordinates for the 265 TLC Taxi Zones
with open("zone_centroids.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["LocationID", "lat", "lon"])
    for i in range(1, 266):
        # Create slight geographical variations for distinct H3 hashes
        writer.writerow([i, 40.7128 + (i * 0.001), -74.0060 - (i * 0.001)])

print("Success! zone_centroids.csv generated.")