import config
from utils_exec import execute_all_steps
from pathlib import Path

# Continent dict that can be used as list
Africa = {'AO': 'Angola', 'BF': 'Burkina Faso', 'BI': 'Burundi', 'BJ': 'Benin', 'BW': 'Botswana', 'CD': 'Democratic Republic of the Congo', 'CF': 'Central African Republic', 'CG': 'Republic of the Congo', 'CI': 'Ivory Coast', 'CM': 'Cameroon', 'CV': 'Cape Verde', 'DJ': 'Djibouti', 'DZ': 'Algeria', 'EG': 'Egypt', 'ER': 'Eritrea', 'ET': 'Ethiopia', 'GA': 'Gabon', 'GH': 'Ghana', 'GM': 'The Gambia', 'GN': 'Guinea', 'GQ': 'Equatorial Guinea', 'GW': 'Guinea-Bissau', 'KE': 'Kenya', 'KM': 'Comoros', 'LR': 'Liberia', 'LS': 'Lesotho', 'LY': 'Libya', 'MA': 'Morocco', 'MG': 'Madagascar', 'ML': 'Mali', 'MR': 'Mauritania', 'MU': 'Mauritius', 'MW': 'Malawi', 'MZ': 'Mozambique', 'NA': 'Namibia', 'NE': 'Niger', 'NG': 'Nigeria', 'RW': 'Rwanda', 'SC': 'Seychelles', 'SD': 'Sudan', 'SL': 'Sierra Leone', 'SN': 'Senegal', 'SO': 'Somalia', 'SS': 'South Sudan', 'ST': 'São Tomé and Príncipe', 'SZ': 'Eswatini', 'TD': 'Chad', 'TG': 'Togo', 'TN': 'Tunisia', 'TZ': 'Tanzania', 'UG': 'Uganda', 'ZA': 'South Africa', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'}
SouthAmerica = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brazil', 'CL': 'Chile', 'CO': 'Colombia', 'EC': 'Ecuador', 'GY': 'Guyana', 'PA': 'Panama', 'PE': 'Peru', 'PY': 'Paraguay', 'SR': 'Suriname', 'UY': 'Uruguay', 'VE': 'Venezuela'}
SouthAmerica_light = {'AR': 'Argentina', 'BO': 'Bolivia', 'CL': 'Chile', 'CO': 'Colombia', 'EC': 'Ecuador', 'GY': 'Guyana', 'PA': 'Panama', 'PE': 'Peru', 'PY': 'Paraguay', 'SR': 'Suriname', 'UY': 'Uruguay', 'VE': 'Venezuela'}
Asia = {'AE': 'United Arab Emirates', 'AF': 'Afghanistan', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BD': 'Bangladesh', 'BH': 'Bahrain', 'BN': 'Brunei', 'BT': 'Bhutan', 'CN': "People's Republic of China", 'ID': 'Indonesia', 'IL': 'Israel', 'IN': 'India', 'IQ': 'Iraq', 'IR': 'Iran', 'JO': 'Jordan', 'JP': 'Japan', 'KG': 'Kyrgyzstan', 'KH': 'Cambodia', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait', 'KZ': 'Kazakhstan', 'LA': 'Laos', 'LB': 'Lebanon', 'LK': 'Sri Lanka', 'MM': 'Myanmar', 'MN': 'Mongolia', 'MV': 'Maldives', 'MY': 'Malaysia', 'NP': 'Nepal', 'OM': 'Oman', 'PH': 'Philippines', 'PK': 'Pakistan', 'PS': 'State of Palestine', 'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SG': 'Singapore', 'SY': 'Syria', 'TH': 'Thailand', 'TJ': 'Tajikistan', 'TL': 'Timor-Leste', 'TM': 'Turkmenistan', 'TR': 'Turkey', 'TW': 'Taiwan', 'UZ': 'Uzbekistan', 'VN': 'Vietnam', 'YE': 'Yemen'}
Asia_light = {'AE': 'United Arab Emirates', 'AF': 'Afghanistan', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BD': 'Bangladesh', 'BH': 'Bahrain', 'BN': 'Brunei', 'BT': 'Bhutan', 'ID': 'Indonesia', 'IL': 'Israel', 'IQ': 'Iraq', 'IR': 'Iran', 'JO': 'Jordan', 'JP': 'Japan', 'KG': 'Kyrgyzstan', 'KH': 'Cambodia', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait', 'KZ': 'Kazakhstan', 'LA': 'Laos', 'LB': 'Lebanon', 'LK': 'Sri Lanka', 'MM': 'Myanmar', 'MN': 'Mongolia', 'MV': 'Maldives', 'MY': 'Malaysia', 'NP': 'Nepal', 'OM': 'Oman', 'PH': 'Philippines', 'PK': 'Pakistan', 'PS': 'State of Palestine', 'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SG': 'Singapore', 'SY': 'Syria', 'TH': 'Thailand', 'TJ': 'Tajikistan', 'TL': 'Timor-Leste', 'TM': 'Turkmenistan', 'TR': 'Turkey', 'TW': 'Taiwan', 'UZ': 'Uzbekistan', 'VN': 'Vietnam', 'YE': 'Yemen'}
Oceania = {'AU': 'Australia', 'FJ': 'Fiji', 'FM': 'Federated States of Micronesia', 'KI': 'Kiribati', 'MH': 'Marshall Islands', 'NR': 'Nauru', 'NZ': 'New Zealand', 'PG': 'Papua New Guinea', 'PW': 'Palau', 'SB': 'Solomon Islands', 'TO': 'Tonga', 'TV': 'Tuvalu', 'VU': 'Vanuatu', 'WS': 'Samoa'}
NorthAmerica = {'AG': 'Antigua and Barbuda', 'BB': 'Barbados', 'BS': 'The Bahamas', 'BZ': 'Belize', 'CA': 'Canada', 'CR': 'Costa Rica', 'CU': 'Cuba', 'DM': 'Dominica', 'DO': 'Dominican Republic', 'GD': 'Grenada', 'GT': 'Guatemala', 'HN': 'Honduras', 'HT': 'Haiti', 'JM': 'Jamaica', 'KN': 'Saint Kitts and Nevis', 'LC': 'Saint Lucia', 'MX': 'Mexico', 'NI': 'Nicaragua', 'SV': 'El Salvador', 'TT': 'Trinidad and Tobago', 'US': 'United States', 'VC': 'Saint Vincent and the Grenadines'}
NorthAmerica_light = {'AG': 'Antigua and Barbuda', 'BB': 'Barbados', 'BS': 'The Bahamas', 'BZ': 'Belize', 'CA': 'Canada', 'CR': 'Costa Rica', 'CU': 'Cuba', 'DM': 'Dominica', 'DO': 'Dominican Republic', 'GD': 'Grenada', 'GT': 'Guatemala', 'HN': 'Honduras', 'HT': 'Haiti', 'JM': 'Jamaica', 'KN': 'Saint Kitts and Nevis', 'LC': 'Saint Lucia', 'MX': 'Mexico', 'NI': 'Nicaragua', 'SV': 'El Salvador', 'TT': 'Trinidad and Tobago', 'VC': 'Saint Vincent and the Grenadines'}
Europe = {'AD': 'Andorra', 'AL': 'Albania', 'AT': 'Austria', 'BA': 'Bosnia and Herzegovina', 'BE': 'Belgium', 'BG': 'Bulgaria', 'BY': 'Belarus', 'CH': 'Switzerland', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DE': 'Germany', 'DK': 'Kingdom of Denmark', 'EE': 'Estonia', 'ES': 'Spain', 'FI': 'Finland', 'FR': 'France', 'GB': 'United Kingdom', 'GE': 'Georgia', 'GR': 'Greece', 'HR': 'Croatia', 'HU': 'Hungary', 'IE': 'Ireland', 'IS': 'Iceland', 'IT': 'Italy', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg', 'LV': 'Latvia', 'MC': 'Monaco', 'MD': 'Moldova', 'ME': 'Montenegro', 'MK': 'North Macedonia', 'MT': 'Malta', 'NL': 'Kingdom of the Netherlands', 'NO': 'Norway', 'PL': 'Poland', 'PT': 'Portugal', 'RO': 'Romania', 'RS': 'Serbia', 'RU': 'Russia', 'SE': 'Sweden', 'SI': 'Slovenia', 'SK': 'Slovakia', 'SM': 'San Marino', 'UA': 'Ukraine', 'VA': 'Vatican City'}
Europe_light = {'AD': 'Andorra', 'AL': 'Albania', 'AT': 'Austria', 'BA': 'Bosnia and Herzegovina', 'BE': 'Belgium', 'BG': 'Bulgaria', 'BY': 'Belarus', 'CH': 'Switzerland', 'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Kingdom of Denmark', 'EE': 'Estonia', 'ES': 'Spain', 'FI': 'Finland', 'GE': 'Georgia', 'GR': 'Greece', 'HR': 'Croatia', 'HU': 'Hungary', 'IE': 'Ireland', 'IS': 'Iceland', 'IT': 'Italy', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg', 'LV': 'Latvia', 'MC': 'Monaco', 'MD': 'Moldova', 'ME': 'Montenegro', 'MK': 'North Macedonia', 'MT': 'Malta', 'NL': 'Kingdom of the Netherlands', 'NO': 'Norway', 'PL': 'Poland', 'PT': 'Portugal', 'RO': 'Romania', 'RS': 'Serbia', 'SE': 'Sweden', 'SI': 'Slovenia', 'SK': 'Slovakia', 'SM': 'San Marino', 'UA': 'Ukraine', 'VA': 'Vatican City'}

# No Brazil, China and India in light dict
COUNTRY_LIST = config.WORLD_COUNTRY_DICT #{'CO': 'Colombia'}
COUNTRY_LIST = config.CONTINENTAL_COUNTRY_DICT["Africa"]
COUNTRY_LIST =  {'BG': 'Bulgaria'}

# Processing -----------------------
list_errors = {}

selfpathfolder = Path(__file__).parent

for code, name in COUNTRY_LIST.items():
    print(f"> Starting execution for {name} ({code})")
    # Run scripts
    try:
        execute_all_steps(code)
    except Exception as e:
        print("SCRIPT ERROR", e)
        list_errors[code] = name
    print(f"> End {code}\n")

print("\nEnd of processing country lists")
if list_errors:
    print("Errors have been encountered for the following countries = ", list_errors)
