#!/usr/bin/env python
import sys
import io
import os
import os.path
import itertools
import json

import email

import dateutil.parser
import datetime
import pytz

import logging
import argparse


def to_camel_case(v):
    """
    Convert keys with hyphens to camelcase so we can use Dataset schema inference in Spark 2.0.
    See README.md for more details.
    """
    parts = v.split('-')
    return parts[0] + "".join(x.title() for x in parts[1:])


def parse_cats(f):
    """
    Format of each line in .cats file:
    n1,n2,n3

    n1 = top-level category
    n2 = second-level category
    n3 = frequency with which this category was assigned to this message
    """

    categories = []
    for line in f:
        cat_arr = line.rstrip('\r\n').split(',')
        categories.append({
            'n1': cat_arr[0],
            'n2': cat_arr[1],
            # Omitting frequency due to Spark Dataset nested array bug
            # https://issues.apache.org/jira/browse/SPARK-14034
            # 'frequency': cat_arr[2]
        })
    return categories


def parse_email(email_id, f):
    """
    :param email_id:
    :param f:
    :return:
    """
    raw = f.read()
    doc = {'id': email_id}

    # Parse the email using the Python email module and save fields
    e = email.message_from_string(raw)

    if e.is_multipart():
        logging.warn("Email is multipart, skipping.")
        return None

    # Add the email fields with lowercase keys to the document
    doc = dict(doc.items() + [(k.lower(), v) for k, v in e.items()])

    # Standarize the date field to UTC
    doc['dateRaw'] = doc['date']
    doc['date'] = dateutil.parser.parse(doc['date'])
    doc['date'] = doc['date'].astimezone(pytz.utc).isoformat()

    # Clean up and split recipients fields
    for field in ['to', 'x-to', 'cc', 'x-cc', 'bcc', 'x-bcc']:
        if field not in doc or doc[field] is None:
            doc[field] = []
        else:
            doc[field] = [
                addr.strip()
                for addr in doc.get(field, "").split(',')
                if len(addr.strip()) > 0
            ]

    # Set flag based on whether there's a recipient in the email
    doc['noRecipient'] = len(doc['to']) == 0 and len(doc['cc']) == 0 and len(doc['bcc']) == 0
    if doc['noRecipient']:
        logging.warn("%s has no recipient in [to, cc, bcc]. "
                     "Setting 'noRecipient' flag.", email_id)

    # Add the payload
    doc['body'] = e.get_payload()

    # Remove newline from the subject and trim whitespace
    doc['subject'] = doc['subject'].replace('\r', '').replace('\n', '').strip()

    # camelcase keys for compatibility with Spark Dataset deserialization magic
    doc = {to_camel_case(k): v for k, v in doc.iteritems()}
    return doc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir')
    parser.add_argument('out_file')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    with io.open(args.out_file, 'wb') as out:
        # Walk through all files within the directory
        for (root_path, _, filenames) in os.walk(args.in_dir):

            # Group files by the name without its file extension
            for (_, file_iter) in itertools.groupby(sorted(filenames), lambda x: os.path.splitext(x)[0]):
                files = list(file_iter)

                if files == ['categories.txt']:
                    # We'll skip categories.txt that ships with the tar.gz
                    continue

                try:
                    # Check if there's a file that ends with .cats
                    cats_filename = next((f for f in files if f.endswith('.cats')), None)
                    email_filename = next((f for f in files if f != cats_filename), None)

                    if email_filename is None:
                        logging.warn("Category file %s has no corresponding email file, continuing.", cats_filename)
                        continue

                    with io.open(os.path.join(root_path, email_filename), 'rb') as f:
                        doc = parse_email(email_filename, f)

                    if cats_filename is not None:
                        with io.open(os.path.join(root_path, cats_filename), 'rb') as f:
                            doc['categories'] = parse_cats(f)
                    else:
                        doc['categories'] = []

                    # Write output
                    if doc is not None:
                        json.dump(doc, out, ensure_ascii=False)
                        out.write('\n')
                    else:
                        logging.warn("Missing .txt or .cats file for: %s", list(files))
                except Exception as e:
                    logging.error("Failed to parse group: %s", files)
                    logging.exception(e)

        logging.info("Output written to %s", args.out_file)


if __name__ == '__main__':
    main()
