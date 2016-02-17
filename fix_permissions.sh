#!/bin/bash

script_dir=$( cd "`dirname $0`" && pwd )
cd "$script_dir"
chgrp -R grader .
find . -type f -exec chmod g+rw {} \;
find . -type d -exec chmod g+rwx {} \;
