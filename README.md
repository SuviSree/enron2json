# Enron to JSON Dataset Converter

The enron email dataset with labelled categories is organized as directories of raw email text. This script parses the email headers and labelled categories and outputs it as a JSON file where each line is a JSON object for an email.

## Usage

First, download the `enron_with_categories` dataset from the UC Berkeley site. Run this script to download the tar.gz into the current working directory:

```
$ bin/download_enron_with_categories.sh
```

Next, unpack the tar.gz with this script:
```
$ bin/unpack_enron_with_categories.sh
```

Now, run the parser with this command:
```
$ python load.py enron_with_categories/ enron.json
```

Where `enron_with_categories/` is the directory where the dataset is extracted, and `enron.json` is the output filename.

## Output Format

This tool outputs one email per line in the resulting JSON file.

Each line in the output JSON file represents an email and will have the following fields:
```json
{
  "id": "115905.txt",
  "from": "...",
  "to": [
    "..."
  ],
  "cc": [],
  "bcc": [],
  "subject": "..",
  "contentTransferEncoding": "7bit",
  "dateRaw": "Wed, 4 Oct 2000 11:53:00 -0700 (PDT)",
  "mimeVersion": "1.0",
  "body": "...",
  "messageId": "<8217324.1075842988636.JavaMail.evans@thyme>",
  "contentType": "text/plain; charset=us-ascii",
  "noRecipient": false,
  "date": "2000-10-04T18:53:00+00:00",
  "categories": [
    {
      "n1": "1",
      "n2": "7"
    },
    {
      "n1": "2",
      "n2": "13"
    }
  ],
  "xBcc": [],
  "xCc": [],
  "xFilename": "...",
  "xFrom": "Firstname Lastname",
  "xOrigin": "DASOVICH-J",
  "xTo": [
    "Firstname Lastname"
  ],
  "xFolder": "\\...\\Notes Folders\\All documents",
}
```

The special `noRecipient` field identifies emails where the `to`, `cc`, or `bcc` fields are empty.
