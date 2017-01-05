#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR/..
curl -O http://bailando.sims.berkeley.edu/enron/enron_with_categories.tar.gz
