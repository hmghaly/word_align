#!/bin/bash
git init
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts
git pull --rebase git@github.com:hmghaly/alif2.git master
git add .
git commit -m "Update existing file"
git push --mirror git@github.com:hmghaly/word_align.git
