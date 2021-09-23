#!/bin/bash
curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(dirname "${curr_dir}")

cd ${top_dir}
echo "Use pylint scan code..."
find . -iname "*.py" | xargs pylint

echo "Use bandit scan code..."
bandit -r .
