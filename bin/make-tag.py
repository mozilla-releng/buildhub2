#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import subprocess


def _check_output(*args, **kwargs):
    return subprocess.check_output(*args, **kwargs).decode("utf-8").strip()


def run():
    # Let's make sure we're up-to-date and on master branch
    current_branch = _check_output("git rev-parse --abbrev-ref HEAD".split())
    if current_branch != "master":
        print(f"Must be on the master branch to do this (not {current_branch})")
        return 1

    # The current branch can't be dirty
    try:
        subprocess.check_call("git diff --quiet --ignore-submodules HEAD".split())
    except subprocess.CalledProcessError:
        print(
            "Can't be \"git dirty\" when we're about to git pull. "
            "Stash or commit what you're working on."
        )
        return 2

    # Make sure we have all the old git tags
    _check_output("git pull origin master --tags".split(), stderr=subprocess.STDOUT)

    # Get the last tag
    # We're going to use the last tag to help you write a tag message
    last_tag = _check_output(
        [
            "git",
            "for-each-ref",
            "--sort=-taggerdate",
            "--count=1",
            "--format",
            "%(tag)",
            "refs/tags",
        ]
    )
    last_tag_message = _check_output(["git", "tag", "-l", "--format=%(tag) %(contents)", last_tag])

    print(">>> Last tag was: {}".format(last_tag))
    print(">>> Message:")
    print(last_tag_message)
    print("=" * 80)

    message = _check_output(
        "git log {last_tag}..HEAD --oneline".format(last_tag=last_tag).split()
    )
    # Take out Merge commit lines
    message = '\n'.join([
        line for line in message.splitlines()
        if not line[8:].startswith('Merge pull request')
    ])

    # Next, come up with the next tag name.
    # Normally it's today's date in ISO format with dots.
    tag_name = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    # But is it taken, if so how many times has it been taken before?
    existing_tags = _check_output(
        ["git", "tag", "-l", "{}*".format(tag_name)]
    ).splitlines()
    if existing_tags:
        count_starts = len([x for x in existing_tags if x.startswith(tag_name)])
        tag_name += "-{}".format(count_starts + 1)

    # Now we need to figure out what's been
    print(">>> New tag: %s" % tag_name)
    print(">>> Tag message:")
    print("=" * 80)
    print(message)
    print("=" * 80)

    # Create tag
    input(">>> Ready to tag? Ctrl-c to cancel")
    print(">>> Creating tag...")
    subprocess.check_call(["git", "tag", "-s", tag_name, "-m", message])

    # Push
    input(">>> Ready to push to origin? Ctrl-c to cancel")
    print(">>> Pushing...")
    subprocess.check_call("git push origin master --tags".split())


if __name__ == "__main__":
    import sys

    sys.exit(run())
