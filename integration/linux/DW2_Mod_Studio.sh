#!/bin/sh
# DW2 Mod Studio for Linux x64. Start this script (or DW2_3D_Viewer_Studio directly).
# The interface language follows the system language (German or English) and can be
# changed in the app. If the 3D view stays black on an old graphics driver, start with
#   DW2_SOFTWARE_GL=1 ./DW2_Mod_Studio.sh
here="$(cd "$(dirname "$0")" && pwd)"
if [ -n "$DW2_SOFTWARE_GL" ]; then
  export QTWEBENGINE_CHROMIUM_FLAGS="$QTWEBENGINE_CHROMIUM_FLAGS --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader"
fi
exec "$here/DW2_3D_Viewer_Studio" "$@"
