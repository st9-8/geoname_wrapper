import argparse
from enums import CONTINENTS
from enums import FEATURE_CLASSES

from utils import scrape_geonames
from utils import to_pythonic_string


def main():
    parser = argparse.ArgumentParser(
        description='Scrape and filter geographical data from http://www.geonames.org/, and save it in output file.',
    )

    # Continent
    continent_choices = list(CONTINENTS.values())
    parser.add_argument(
        '-ct', '--continent',
        required=False,
        choices=continent_choices,
        default='',
        help=f"Continent code. Default: ''",
        type=str
    )
    # Country code
    parser.add_argument(
        '-c', '--country',
        required=False,
        help="ISO Code of your country (e.g: CM for Cameroon). Default: ''",
        type=str,
        default=''
    )

    # Feature class / Data type (Optional)
    feature_class_choices = list(FEATURE_CLASSES.keys())
    parser.add_argument(
        '-f', '--feature-class',
        default='city',
        choices=feature_class_choices,
        help=f"Type of feature to search for. Default: city",
        type=str
    )

    # Fields
    default_fields = ['name', 'country', 'feature_class', 'latitude', 'longitude']
    parser.add_argument(
        '-s', '--fields',
        nargs='+',
        default=['name', 'latitude', 'longitude'],
        help='List of fields to include in the output (e.g, name, latitude)',
        type=str
    )

    # Output format
    format_choices = ['csv', 'json', 'raw']
    parser.add_argument(
        '-o', '--output-format',
        default='json',
        choices=format_choices,
        help=f"The output format. Default: json",
        type=str
    )

    # Limit
    parser.add_argument(
        '-l', '--limit',
        default=100,
        help='The number of items to retrieve',
        type=int
    )

    args = parser.parse_args()

    # User fields. We convert them for precaution
    user_fields = [to_pythonic_string(f) for f in args.fields]

    scrape_geonames(
        country_code=args.country,
        continent=args.continent,
        feature_class=args.feature_class,
        fields=user_fields,
        output_format=args.output_format,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
