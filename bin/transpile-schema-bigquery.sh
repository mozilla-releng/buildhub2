#!/bin/bash
: << EOF
# Create a BigQuery table schema from a valid JSONSchema. If all dependencies
# are already installed, you may choose to run this one liner instead.

cat schema.yaml | \
python3 -c 'import json, sys, yaml; y=yaml.safe_load(sys.stdin.read()); print(json.dumps(y))' | \
jq '.schema' | \
jsonschema-transpiler --type bigquery --resolve panic > schema.bigquery.json
EOF

set -e

function check_dependencies() {
    if ! python3 -c "import yaml"; then
        echo "run 'pip install pyyaml'"
        exit 1
    fi

    if ! command -v jsonschema-transpiler; then
        echo "run 'cargo install jsonschema-transpiler'"
        exit 1
    fi
}

function schema_to_json() {
    python3 - <<END
import json
import yaml

with open("schema.yaml", "r") as fp:
    data = yaml.safe_load(fp)

print(json.dumps(data["schema"]))
END
}

check_dependencies
cd "$(dirname "$0")/.."

schema_to_json | \
jsonschema-transpiler --type bigquery --resolve panic > "schema.bigquery.json"
