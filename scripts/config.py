from pathlib import Path

LOG_LEVEL = "ERROR"
SOURCE = "overpass" # either "podoma" or "overpass". Podoma works only if an instance is available.

OSM_POWER_TAGS = ["ref", "name", "type", "route", "power", "voltage", "substation", "line", "circuits", "cables", "wires", "operator", "operator:wikidata", "location", "note", "wikidata", "topology", "frequency"]

COUNTRY_CODE = "EG"
DATA_PATH = Path(__file__).parent.parent / "databox/shapes/"
DATA_PATH.mkdir(exist_ok=True, parents=True)
ERRORS_PATH = Path(__file__).parent.parent / "databox/gridmap_errors/"
ERRORS_PATH.mkdir(exist_ok=True, parents=True)

BUFFER_DISTANCE = 50 # Ideally 0, but all lines are not always well connected to substations

LIST_COUNTRY_CODES = ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AT', 'AU', 'AZ', 'BA', 'BB', 'BD',
                      'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BM', 'BN', 'BO', 'BR', 'BS', 'BT', 'BW', 'BY', 'BZ', 'CA',
                      'CD', 'CF', 'CG', 'CH', 'CI', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CY', 'CZ', 'DE', 'DJ',
                      'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO',
                      'FR', 'GA', 'GB', 'GD', 'GE', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GQ', 'GR', 'GS', 'GT', 'GW',
                      'GY', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE',
                      'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB',
                      'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MG', 'MH', 'MK',
                      'ML', 'MM', 'MN', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NG',
                      'NI', 'NL', 'NO', 'NP', 'NR', 'NZ', 'OM', 'PA', 'PE', 'PG', 'PH', 'PK', 'PL', 'PN', 'PS', 'PT',
                      'PW', 'PY', 'QA', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SK',
                      'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SY', 'SZ', 'TC', 'TD', 'TG', 'TH', 'TJ', 'TL',
                      'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE',
                      'VG', 'VN', 'VU', 'WS', 'XK', 'YE', 'ZA', 'ZM', 'ZW']

CONTINENTAL_COUNTRY_DICT = {
    'Europe': {'AD': 'Andorra', 'AL': 'Albania', 'AT': 'Austria', 'BA': 'Bosnia and Herzegovina', 'BE': 'Belgium',
               'BG': 'Bulgaria', 'BY': 'Belarus', 'CH': 'Switzerland', 'CY': 'Cyprus', 'CZ': 'Czech Republic',
               'DE': 'Germany', 'DK': 'Denmark', 'EE': 'Estonia', 'ES': 'Spain', 'FI': 'Finland', 'FO': 'Faroe Islands',
               'FR': 'France', 'GB': 'United Kingdom', 'GE': 'Georgia', 'GG': 'Guernsey', 'GI': 'Gibraltar',
               'GR': 'Greece', 'HR': 'Croatia', 'HU': 'Hungary', 'IE': 'Ireland', 'IM': 'Isle of Man', 'IS': 'Iceland',
               'IT': 'Italy', 'JE': 'Jersey', 'KZ': 'Kazakhstan', 'LI': 'Liechtenstein', 'LT': 'Lithuania',
               'LU': 'Luxembourg', 'LV': 'Latvia', 'MC': 'Monaco', 'MD': 'Moldova', 'ME': 'Montenegro',
               'MK': 'North Macedonia', 'MT': 'Malta', 'NL': 'Kingdom of the Netherlands', 'NO': 'Norway',
               'PL': 'Poland', 'PT': 'Portugal', 'RO': 'Romania', 'RS': 'Serbia', 'RU': 'Russia', 'SE': 'Sweden',
               'SI': 'Slovenia', 'SK': 'Slovakia', 'SM': 'San Marino', 'UA': 'Ukraine', 'VA': 'Vatican City',
               'XK': 'Kosovo'},
    'Asia': {'AE': 'United Arab Emirates', 'AF': 'Afghanistan', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BD': 'Bangladesh',
             'BH': 'Bahrain', 'BN': 'Brunei', 'BT': 'Bhutan', 'CN': "People's Republic of China", 'ID': 'Indonesia',
             'IL': 'Israel', 'IN': 'India', 'IQ': 'Iraq', 'IR': 'Iran', 'JO': 'Jordan', 'JP': 'Japan',
             'KG': 'Kyrgyzstan', 'KH': 'Cambodia', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait',
             'LA': 'Laos', 'LB': 'Lebanon', 'LK': 'Sri Lanka', 'MM': 'Myanmar', 'MN': 'Mongolia', 'MV': 'Maldives',
             'MY': 'Malaysia', 'NP': 'Nepal', 'OM': 'Oman', 'PH': 'Philippines', 'PK': 'Pakistan', 'PS': 'Palestine',
             'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SG': 'Singapore', 'SY': 'Syria', 'TH': 'Thailand',
             'TJ': 'Tajikistan', 'TL': 'Timor-Leste', 'TM': 'Turkmenistan', 'TR': 'Turkey', 'TW': 'Taiwan',
             'UZ': 'Uzbekistan', 'VN': 'Vietnam', 'YE': 'Yemen'},
    'North America': {'AG': 'Antigua and Barbuda', 'AI': 'Anguilla', 'BB': 'Barbados', 'BM': 'Bermuda',
                      'BS': 'The Bahamas', 'BZ': 'Belize', 'CA': 'Canada', 'CR': 'Costa Rica', 'CU': 'Cuba',
                      'DM': 'Dominica', 'DO': 'Dominican Republic', 'GD': 'Grenada', 'GL': 'Greenland',
                      'GT': 'Guatemala', 'HN': 'Honduras', 'HT': 'Haiti', 'JM': 'Jamaica',
                      'KN': 'Saint Kitts and Nevis', 'KY': 'Cayman Islands', 'LC': 'Saint Lucia', 'MS': 'Montserrat',
                      'MX': 'Mexico', 'NI': 'Nicaragua', 'PA': 'Panama', 'SV': 'El Salvador',
                      'TC': 'Turks and Caicos Islands', 'TT': 'Trinidad and Tobago', 'US': 'United States',
                      'VC': 'Saint Vincent and the Grenadines', 'VG': 'British Virgin Islands'},
    'Africa': {'AO': 'Angola', 'BF': 'Burkina Faso', 'BI': 'Burundi', 'BJ': 'Benin', 'BW': 'Botswana',
               'CD': 'Democratic Republic of the Congo', 'CF': 'Central African Republic',
               'CG': 'Republic of the Congo', 'CI': 'Ivory Coast', 'CM': 'Cameroon', 'CV': 'Cape Verde',
               'DJ': 'Djibouti', 'DZ': 'Algeria', 'EG': 'Egypt', 'EH': 'Western Sahara', 'ER': 'Eritrea',
               'ET': 'Ethiopia', 'GA': 'Gabon', 'GH': 'Ghana', 'GM': 'The Gambia', 'GN': 'Guinea',
               'GQ': 'Equatorial Guinea', 'GW': 'Guinea-Bissau', 'IO': 'British Indian Ocean Territory', 'KE': 'Kenya',
               'KM': 'Comoros', 'LR': 'Liberia', 'LS': 'Lesotho', 'LY': 'Libya', 'MA': 'Morocco', 'MG': 'Madagascar',
               'ML': 'Mali', 'MR': 'Mauritania', 'MU': 'Mauritius', 'MW': 'Malawi', 'MZ': 'Mozambique', 'NA': 'Namibia',
               'NE': 'Niger', 'NG': 'Nigeria', 'RW': 'Rwanda', 'SC': 'Seychelles', 'SD': 'Sudan',
               'SH': 'Saint Helena, Ascension and Tristan da Cunha', 'SL': 'Sierra Leone', 'SN': 'Senegal',
               'SO': 'Somalia', 'SS': 'South Sudan', 'ST': 'São Tomé and Príncipe', 'SZ': 'Eswatini', 'TD': 'Chad',
               'TG': 'Togo', 'TN': 'Tunisia', 'TZ': 'Tanzania', 'UG': 'Uganda', 'ZA': 'South Africa', 'ZM': 'Zambia',
               'ZW': 'Zimbabwe'},
    'Antarctica': {'AQ': 'Antarctica'},
    'South America': {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brazil', 'CL': 'Chile', 'CO': 'Colombia',
                      'EC': 'Ecuador', 'FK': 'Falkland Islands', 'GS': 'South Georgia and the South Sandwich Islands',
                      'GY': 'Guyana', 'PE': 'Peru', 'PY': 'Paraguay', 'SR': 'Suriname', 'UY': 'Uruguay',
                      'VE': 'Venezuela'},
    'Oceania': {'AU': 'Australia', 'FJ': 'Fiji', 'FM': 'Federated States of Micronesia', 'KI': 'Kiribati',
                'MH': 'Marshall Islands', 'NC': 'New Caledonia', 'NR': 'Nauru', 'NZ': 'New Zealand',
                'PG': 'Papua New Guinea', 'PN': 'Pitcairn Islands', 'PW': 'Palau', 'SB': 'Solomon Islands',
                'TO': 'Tonga', 'TV': 'Tuvalu', 'VU': 'Vanuatu', 'WS': 'Samoa'}}

WORLD_COUNTRY_DICT = {}
for continent in CONTINENTAL_COUNTRY_DICT.values():
    WORLD_COUNTRY_DICT = {**WORLD_COUNTRY_DICT, **continent}
