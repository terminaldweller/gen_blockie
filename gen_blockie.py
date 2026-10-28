#!/usr/bin/env python3
"""Generate a blockie PNG from a seed phrase or file contents."""

import argparse
import base64

import blockies


class Argparser:
    """Parse the command-line options."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description=__doc__)
        source = self.parser.add_mutually_exclusive_group()
        source.add_argument("--seed", "-s", type=str, help="seed phrase", default="")
        source.add_argument("--input", "-i", type=str, help="input file path")
        self.parser.add_argument(
            "--out", "-o", default="./identicon.png", help="output PNG path"
        )
        self.parser.add_argument("--fgcolor", "-f", help="foreground color")
        self.parser.add_argument("--bgcolor", "-b", help="background color")
        self.parser.add_argument("--spotcolor", "-p", help="spot color")
        self.parser.add_argument(
            "--size", "-z", type=int, default=10, help="image size in blocks"
        )
        self.parser.add_argument(
            "--scale", "-c", type=int, default=100, help="pixels per block"
        )
        self.args = self.parser.parse_args()


def main() -> None:
    argparser = Argparser()
    args = argparser.args
    if args.size < 1 or args.scale < 1:
        argparser.parser.error("--size and --scale must be positive integers")

    try:
        if args.input is not None:
            with open(args.input, "rb") as source:
                content = source.read()
            if not content:
                argparser.parser.error("input file must not be empty")
            seed = base64.b64encode(content).decode("ascii")
        else:
            seed = args.seed

        data = blockies.create(
            seed=seed,
            size=args.size,
            scale=args.scale,
            color=args.fgcolor,
            bgcolor=args.bgcolor,
            spotcolor=args.spotcolor,
        )
        with open(args.out, "wb") as output:
            output.write(data)
    except (OSError, ValueError) as exc:
        argparser.parser.error(str(exc))


if __name__ == "__main__":
    main()
