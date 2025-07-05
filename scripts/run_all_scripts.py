import config
import shutil
from pathlib import Path

# Cross-script config
config.DATA_PATH = Path(__file__).parent.parent / "data"
config.BUFFER_DISTANCE = 250

# Config for this script
COUNTRY_LIST = {'TZ': 'Tanzania', 'KE': 'Kenya', 'UG': 'Uganda'}

# Continent dict that can be used as list
Africa = {'AO': 'Angola', 'BF': 'Burkina Faso', 'BI': 'Burundi', 'BJ': 'Benin', 'BW': 'Botswana', 'CD': 'Democratic Republic of the Congo', 'CF': 'Central African Republic', 'CG': 'Republic of the Congo', 'CI': 'Ivory Coast', 'CM': 'Cameroon', 'CV': 'Cape Verde', 'DJ': 'Djibouti', 'DZ': 'Algeria', 'EG': 'Egypt', 'ER': 'Eritrea', 'ET': 'Ethiopia', 'GA': 'Gabon', 'GH': 'Ghana', 'GM': 'The Gambia', 'GN': 'Guinea', 'GQ': 'Equatorial Guinea', 'GW': 'Guinea-Bissau', 'KE': 'Kenya', 'KM': 'Comoros', 'LR': 'Liberia', 'LS': 'Lesotho', 'LY': 'Libya', 'MA': 'Morocco', 'MG': 'Madagascar', 'ML': 'Mali', 'MR': 'Mauritania', 'MU': 'Mauritius', 'MW': 'Malawi', 'MZ': 'Mozambique', 'NA': 'Namibia', 'NE': 'Niger', 'NG': 'Nigeria', 'RW': 'Rwanda', 'SC': 'Seychelles', 'SD': 'Sudan', 'SL': 'Sierra Leone', 'SN': 'Senegal', 'SO': 'Somalia', 'SS': 'South Sudan', 'ST': 'São Tomé and Príncipe', 'SZ': 'Eswatini', 'TD': 'Chad', 'TG': 'Togo', 'TN': 'Tunisia', 'TZ': 'Tanzania', 'UG': 'Uganda', 'ZA': 'South Africa', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'}
## SouthAmerica = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brazil', 'CL': 'Chile', 'CO': 'Colombia', 'EC': 'Ecuador', 'GY': 'Guyana', 'PA': 'Panama', 'PE': 'Peru', 'PY': 'Paraguay', 'SR': 'Suriname', 'UY': 'Uruguay', 'VE': 'Venezuela'}
SouthAmerica_light = {'AR': 'Argentina', 'BO': 'Bolivia', 'CL': 'Chile', 'CO': 'Colombia', 'EC': 'Ecuador', 'GY': 'Guyana', 'PA': 'Panama', 'PE': 'Peru', 'PY': 'Paraguay', 'SR': 'Suriname', 'UY': 'Uruguay', 'VE': 'Venezuela'}
## Asia = {'AE': 'United Arab Emirates', 'AF': 'Afghanistan', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BD': 'Bangladesh', 'BH': 'Bahrain', 'BN': 'Brunei', 'BT': 'Bhutan', 'CN': "People's Republic of China", 'ID': 'Indonesia', 'IL': 'Israel', 'IN': 'India', 'IQ': 'Iraq', 'IR': 'Iran', 'JO': 'Jordan', 'JP': 'Japan', 'KG': 'Kyrgyzstan', 'KH': 'Cambodia', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait', 'KZ': 'Kazakhstan', 'LA': 'Laos', 'LB': 'Lebanon', 'LK': 'Sri Lanka', 'MM': 'Myanmar', 'MN': 'Mongolia', 'MV': 'Maldives', 'MY': 'Malaysia', 'NP': 'Nepal', 'OM': 'Oman', 'PH': 'Philippines', 'PK': 'Pakistan', 'PS': 'State of Palestine', 'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SG': 'Singapore', 'SY': 'Syria', 'TH': 'Thailand', 'TJ': 'Tajikistan', 'TL': 'Timor-Leste', 'TM': 'Turkmenistan', 'TR': 'Turkey', 'TW': 'Taiwan', 'UZ': 'Uzbekistan', 'VN': 'Vietnam', 'YE': 'Yemen'}
Asia_light = {'AE': 'United Arab Emirates', 'AF': 'Afghanistan', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BD': 'Bangladesh', 'BH': 'Bahrain', 'BN': 'Brunei', 'BT': 'Bhutan', 'ID': 'Indonesia', 'IL': 'Israel', 'IQ': 'Iraq', 'IR': 'Iran', 'JO': 'Jordan', 'JP': 'Japan', 'KG': 'Kyrgyzstan', 'KH': 'Cambodia', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait', 'KZ': 'Kazakhstan', 'LA': 'Laos', 'LB': 'Lebanon', 'LK': 'Sri Lanka', 'MM': 'Myanmar', 'MN': 'Mongolia', 'MV': 'Maldives', 'MY': 'Malaysia', 'NP': 'Nepal', 'OM': 'Oman', 'PH': 'Philippines', 'PK': 'Pakistan', 'PS': 'State of Palestine', 'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SG': 'Singapore', 'SY': 'Syria', 'TH': 'Thailand', 'TJ': 'Tajikistan', 'TL': 'Timor-Leste', 'TM': 'Turkmenistan', 'TR': 'Turkey', 'TW': 'Taiwan', 'UZ': 'Uzbekistan', 'VN': 'Vietnam', 'YE': 'Yemen'}

# No Brazil, China and India in light dict
# COUNTRY_LIST = { **Africa, **SouthAmerica_light, **Asia_light }

# set it to a two-digit country code to skip all countries until this one (the indicated code will be processed)
# Useful we re-running the script if an error has been encountered, without modifying country list
SKIP_LIST_UNTIL = None

# Processing -----------------------
list_errors = []
flag_skip = (SKIP_LIST_UNTIL is not None) # Set to True to skip countries

selfpathfolder = Path(__file__).parent

for code, name in COUNTRY_LIST.items():
    if flag_skip:
        if SKIP_LIST_UNTIL == code:
            flag_skip = False
        else:
            continue #Skip until country code
    print(f"> Starting execution for {name} ({code})")
    config.COUNTRY_CODE = code

    # Run scripts
    try:
        print(">> Step1 - Download data")
        exec(open(selfpathfolder / "step1_download_data_overpass.py").read())
        print(">> Step2 - Prepare for graph")
        exec(open(selfpathfolder / "step2_prepare_for_graph.py").read())
        print(">> Step3 - Build graph and analyse connectivity")
        exec(open(selfpathfolder / "step3_build_graph.py").read())
    except Exception as e:
        print("SCRIPT ERROR", e)
        list_errors.append((code, name))
    print(f"> End {code}\n")

print("\nEnd of processing country lists")
if list_errors:
    print("Errors have been encountered for the following countries = ", list_errors)
