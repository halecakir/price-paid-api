"""Populate Database
Usage:
  populate_db.py --price-paid-data=<str> --db-table-name=<str> --db-name=<str> --db-user=<str> --db-pass=<str> --db-host=<str>
  populate_db.py (-h | --help)

Example, try:
  python populate_db.py -pp=pp-completed.csv -tn=pricepaid -db=mydb -u=myuser -p=secret -hn=localhost

Options:
  -h --help                                  Show this screen.
  -pp, --price-paid-data=<str>               Price paid data file name.
  -tn, --db-table-name=<str>                 DB table to be populated.
  -db, --db-name=<str>                       DB name.
  -u, --db-user=<str>                        DB user.
  -p, --db-pass=<str>                        DB password.
  -hn, --db-host=<str>                       DB hostname.
"""


import os
from io import StringIO

import pandas as pd
import psycopg2
from docopt import docopt
from tqdm import tqdm

PP_DATA_COLUMN_NAMES = [
    "Transaction unique identifier",
    "Price",
    "Date of Transfer",
    "Postcode",
    "Property Type",
    "Old/New",
    "Duration",
    "PAON",
    "SAON",
    "Street",
    "Locality",
    "Town/City",
    "District",
    "County",
    "PPD Category Type",
    "Record Status",
]

CHUNK_SIZE = 10000


def copy_from_stringio(conn, df, table):
    """
    Here we are going save the dataframe in memory
    and use copy_from() to copy it to the table
    """
    # save dataframe to an in memory buffer
    buffer = StringIO()
    df.to_csv(buffer, index_label="id", header=False)
    buffer.seek(0)

    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, table, sep=",")
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    cursor.close()


def connect_postgres(params_dic):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params_dic)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1)
    print("Connection successful")
    return conn


def main(db_info, table_name, csv_file):
    conn = connect_postgres(db_info)
    for chunk in tqdm(
        pd.read_csv(
            csv_file,
            names=PP_DATA_COLUMN_NAMES,
            usecols=["Postcode", "Property Type", "Price", "Date of Transfer"],
            chunksize=CHUNK_SIZE,
        )
    ):
        chunk.rename(
            columns={
                "Date of Transfer": "transfer_date",
                "Property Type": "property_type",
                "Postcode": "postal_code",
                "Price": "price",
            },
            inplace=True,
        )
        chunk = chunk[chunk["postal_code"].notna()]
        chunk = chunk[["postal_code", "property_type", "price", "transfer_date"]]
        copy_from_stringio(conn, chunk, table_name)


if __name__ == "__main__":
    args = docopt(__doc__)

    db_info = {
        "host": args["--db-host"],
        "database": args["--db-name"],
        "user": args["--db-user"],
        "password": args["--db-pass"],
    }

    assert os.path.exists(
        args["--price-paid-data"]
    ), f"Price paid file {args['--price-paid-data']} does not exist!"

    main(db_info, args["--db-table-name"], args["--price-paid-data"])
