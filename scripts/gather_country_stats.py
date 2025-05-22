"""
Gather all data from generated power grid graph analysis (step3 output) in a single CSV file
"""

import json
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).parent.parent / "data"
EXPORT_FILEPATH = Path(__file__).parent.parent / "export/powergrid_analysis_countries_info.csv"
STATS_FILENAME = "power_grid_stats.json"

countrylist = ["AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ", "BH", "BD", "BB", "BY", "BE", "BZ",
               "BJ", "BT", "BO", "BA", "BW", "BR", "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CV", "CF", "TD", "CL",
               "CO", "KM", "CR", "HR", "CU", "CY", "CZ", "CD", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE",
               "SZ", "ET", "FM", "FJ", "FI", "FR", "GA", "GE", "DE", "GH", "GR", "GD", "GT", "GN", "GW", "GY", "HT",
               "HN", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IL", "IT", "CI", "JM", "JP", "JO", "KZ", "KE", "NL",
               "KI", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MG", "MW", "MY", "MV", "ML",
               "MT", "MH", "MR", "MU", "MX", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA", "NR", "NP", "NZ", "NI",
               "NE", "NG", "KP", "MK", "NO", "OM", "PK", "PW", "PA", "PG", "PY", "CN", "PE", "PH", "PL", "PT", "QA",
               "CG", "RO", "RU", "RW", "KN", "LC", "VC", "WS", "SM", "SA", "SN", "RS", "SC", "SL", "SG", "SK", "SI",
               "SB", "SO", "ZA", "KR", "SS", "ES", "LK", "PS", "SD", "SR", "SE", "CH", "SY", "ST", "TW", "TJ", "TZ",
               "TH", "BS", "GM", "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TV", "UG", "UA", "AE", "GB", "US", "UY",
               "UZ", "VU", "VA", "VE", "VN", "YE", "ZM", "ZW"]

# Processing
result = []
for country in countrylist:
    mypath = DATA_PATH / f"{country}/{STATS_FILENAME}"
    print(mypath)
    if mypath.is_file():
        with open(mypath) as f:
            y = json.load(f)
            result.append({"codeiso2":country, **y})
    else:
        result.append({"codeiso2": country})

df = pd.DataFrame(result)
df.to_csv(EXPORT_FILEPATH, index=False)
