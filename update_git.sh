#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "${DIR}"
git add .
git commit -m "Update existing file"
git push --mirror git@github.com:hmghaly/word_align.git
