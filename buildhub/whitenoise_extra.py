# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import re

from whitenoise.middleware import WhiteNoiseMiddleware


class BuildhubMixin:
    """We serve all the static files that are built from the "ui" create-react-app.
    These files are things like ui/build/static/css/main.8741ee2b.css.
    For these make sure we set full caching.
    """

    regex = re.compile(r"\b[a-f0-9]{8}\b")

    def is_immutable_file(self, path, url):
        return bool(self.regex.search(url))


class BuildhubWhiteNoiseMiddleware(BuildhubMixin, WhiteNoiseMiddleware):
    """Overridden for two reasons:

    1. To able to squeeze in our own method that defines a better "is_immutable_files".
    2. Override on the self.max_age

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # By default the WhiteNoiseMiddleware class uses max_age=60
        # (or max_age=0 if settings.DEBUG).
        # Let's increase that for our case.
        self.max_age = 60 * 60 * 24 * 7  # week
