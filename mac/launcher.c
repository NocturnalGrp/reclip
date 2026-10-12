/* ReClip.app main executable: embeds Homebrew Python and runs desktop.py.
 *
 * A real binary inside the bundle (instead of a shell script exec'ing
 * python) makes macOS treat the process as ReClip: Dock name, icon,
 * Cmd-Tab and Force Quit all show ReClip rather than "Python".
 *
 * PROJECT_DIR and SITE_PACKAGES are passed in by mac/build_app.py.
 */
#include <Python.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    (void)argc;

    if (chdir(PROJECT_DIR) != 0) {
        return 1;
    }
    /* Finder-launched apps get a bare PATH; yt-dlp and ffmpeg live here. */
    setenv("PATH", PROJECT_DIR "/venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin", 1);
    setenv("PYTHONPATH", SITE_PACKAGES, 1);

    char *args[] = {argv[0], "desktop.py", NULL};
    return Py_BytesMain(2, args);
}
