#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o errtrace

# Clear usr.manifest.skel that is already contained in bootstrap package
echo "[manifest]" > ${OSV_DIR}/usr.manifest.skel

echo "Exporting Erlang"

cd ${OSV_DIR}
${OSV_DIR}/scripts/build image=erlang

cd ${OSV_BUILD_DIR}
${OSV_DIR}/scripts/upload_manifest.py -m usr.manifest -e ${PACKAGE_RESULT_DIR} -D gccbase=${GCCBASE} -D miscbase=${MISCBASE}

cd ${PACKAGE_RESULT_DIR}
capstan package init --name "${PACKAGE_NAME}" \
    --title "Erlang" \
    --author "MIKELANGELO Project (info@mikelangelo-project.eu)" \
    --version 18.0

echo "Done"
