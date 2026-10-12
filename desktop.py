"""Run ReClip as a standalone desktop window (pywebview / WKWebView).

Starts the Flask app on a free localhost port in a background thread,
opens it in a native window, and exits when the window is closed.
Downloads save straight to ~/Downloads (no save dialog per file).
"""
import os
import socket
import threading

import AppKit
import Foundation
import webview
from webview.platforms import cocoa
from werkzeug.serving import make_server

from app import app

DOWNLOADS = os.path.expanduser("~/Downloads")
ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mac", "ReClip.icns")


def brand_process():
    # The process is Homebrew's Python, so without this the Dock and
    # menu bar would say "Python" with the rocket icon.
    info = Foundation.NSBundle.mainBundle().infoDictionary()
    info["CFBundleName"] = "ReClip"
    info["CFBundleDisplayName"] = "ReClip"
    nsapp = AppKit.NSApplication.sharedApplication()
    if os.path.exists(ICON):
        nsapp.setApplicationIconImage_(AppKit.NSImage.alloc().initWithContentsOfFile_(ICON))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def unique_path(name):
    base, ext = os.path.splitext(name or "download")
    path = os.path.join(DOWNLOADS, base + ext)
    n = 1
    while os.path.exists(path):
        path = os.path.join(DOWNLOADS, f"{base} ({n}){ext}")
        n += 1
    return path


class ReClipDownloadDelegate(AppKit.NSObject):
    """Replaces pywebview's delegate, which pops a save panel per file."""

    def download_decideDestinationUsingResponse_suggestedFilename_completionHandler_(
        self, download, response, suggested, completion
    ):
        self._path = unique_path(suggested)
        completion(Foundation.NSURL.fileURLWithPath_(self._path))

    def downloadDidFinish_(self, download):
        # Bounce the Downloads stack in the Dock, like a browser does.
        Foundation.NSDistributedNotificationCenter.defaultCenter().postNotificationName_object_(
            "com.apple.DownloadFileFinished", self._path
        )


cocoa.BrowserView.DownloadDelegate = ReClipDownloadDelegate


def main():
    brand_process()
    port = free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.create_window(
        "ReClip",
        f"http://127.0.0.1:{port}/",
        width=900,
        height=820,
        min_size=(520, 500),
    )
    webview.start()
    server.shutdown()


if __name__ == "__main__":
    main()
