#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -eo pipefail

prelude() {
  echo "
You have Prettier linting errors!
----------------------------------
The following files would turn out different if you process them with prettier.

"
}

any=false
first=true
while read line
do
  $first && prelude
  echo "To fix:"
  echo "    prettier --write ${line}"
  echo "To see:"
  echo "    prettier ${line} | diff ${line} -"
  echo ""
  # echo "$line"
  any=true
  first=false
done < "${1:-/dev/stdin}"


$any && echo "
If you're not interested in how they're different, consider running:

  yarn run lint:prettierfix
"

$any && exit 1 || exit 0
