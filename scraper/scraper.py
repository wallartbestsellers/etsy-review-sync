import json
from datetime import datetime

data = {
    "last_updated": str(datetime.utcnow()),
    "shop": "WallArtBestSellers",
    "reviews": [
        {
            "reviewer": "Sample User",
            "rating": 5,
            "text": "Beautiful artwork!",
            "date": "2026-01-01",
            "listing": "Vintage Print"
        }
    ]
}

with open("output/reviews.json", "w") as f:
    json.dump(data, f, indent=2)

print("Reviews exported")
