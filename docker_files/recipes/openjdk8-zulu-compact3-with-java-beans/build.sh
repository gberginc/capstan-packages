#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o errtrace

# Clear usr.manifest.skel that is already contained in bootstrap package
echo "[manifest]" > ${OSV_DIR}/usr.manifest.skel

###############################################################################
# Build the OpenJDK 8 Zulu Compact1 package.
###############################################################################

echo "Exporting OpenJDK 8 Zulu Compact3 With Java Beans"

cd ${OSV_DIR}
${OSV_DIR}/scripts/build image=openjdk8-zulu-compact3-with-java-beans

cd ${OSV_BUILD_DIR}
${OSV_DIR}/scripts/upload_manifest.py -m usr.manifest -e ${PACKAGE_RESULT_DIR} -D gccbase=${GCCBASE} -D miscbase=${MISCBASE}

# Fix "java" empty folder problem
rmdir ${PACKAGE_RESULT_DIR}/usr/lib/jvm/java
mv ${PACKAGE_RESULT_DIR}/usr/lib/jvm/j2re-compact3-with-java-beans-image ${PACKAGE_RESULT_DIR}/usr/lib/jvm/java

cd ${PACKAGE_RESULT_DIR}
capstan package init --name "${PACKAGE_NAME}" \
    --title "OpenJDK 1.8.0_112 zulu-compact3-with-java-beans" \
    --author "MIKELANGELO Project (info@mikelangelo-project.eu)" \
    --version 0.1

echo "Done"
