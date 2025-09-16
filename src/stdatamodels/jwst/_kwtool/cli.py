import argparse
from html.parser import HTMLParser
from pprint import pformat

from .compare import compare_keywords


class ParseHTML(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_kwd = []
        self.in_dmd = []
        self.in_both = []
        self.save_in_kwd = False
        self.save_in_dmd = False
        self.save_in_both = False

    def handle_data(self, data):
        if "Keywords in the keyword dictionary but NOT in the datamodel schemas" in data:
            self.save_in_kwd = True
            self.save_in_dmd = False
            self.save_in_both = False
        elif "Keywords in the datamodel schemas but NOT in the keyword dictionary" in data:
            self.save_in_kwd = False
            self.save_in_dmd = True
            self.save_in_both = False
        elif "Keywords in both with definition differences" in data:
            self.save_in_kwd = False
            self.save_in_dmd = False
            self.save_in_both = True
        if self.save_in_kwd:
            if "HDU:" in data:
                items = data.split()
                self.in_kwd.append((items[1], items[3]))
        elif self.save_in_dmd:
            if "HDU:" in data:
                items = data.split()
                self.in_dmd.append((items[1], items[3]))
        elif self.save_in_both:
            if "HDU:" in data:
                items = data.split()
                self.in_both.append((items[1], items[3]))


def _make_template(tag):
    return f"<{tag}>" + "{0}" + f"</{tag}>"


def _render(tag, txt):
    return _make_template(tag).format(txt)


R = _render


def _keyword_to_str(k):
    hdu, kw = k
    return f"HDU: {hdu}  KEYWORD: {kw}"


def _entry_to_str(entry):
    return R(
        "div",
        R(
            "dl",
            R("dt", "path")
            + R("dd", entry["path"])
            + R("dt", "scope")
            + R("dd", entry["scope"])
            + R("dt", "keyword")
            + R("dd", R("pre", R("code", pformat(entry["keyword"], indent=2)))),
        ),
    )


def _keyword_details(kwd, dmd, k):
    s = ""
    for d, h in [(kwd, "Keyword Dictionary"), (dmd, "Datamodel Schemas")]:
        s += R("h3", h)
        if k not in d:
            s += "Missing"
        else:
            ss = ""
            for entry in d[k]:
                ss += R("li", _entry_to_str(entry))
            s += R("ul", ss)
    return s


def _set_to_list(item):
    if isinstance(item, set):
        return _set_to_list(sorted(item))
    if isinstance(item, (list, tuple)):
        return [_set_to_list(i) for i in item]
    if isinstance(item, dict):
        return {_set_to_list(k): _set_to_list(v) for k, v in item.items()}
    return item


def _diff_format(diff):
    # convert all sets to lists and sort them for consistent output
    return pformat(_set_to_list(diff), indent=2)


def _def_diff_details(d):
    s = ""
    for diff_name, diff in d.items():
        s += R(
            "dl",
            R("dt", diff_name) + R("dd", R("pre", R("code", _diff_format(diff)))),
        )
    return R("div", s)


def read_previous_report(previous_report):
    with open(previous_report, "r") as f:
        rpt = f.read()
        prev_rep = ParseHTML()
        prev_rep.feed(rpt)
    return prev_rep


def check_tuple_exist(the_set, the_tuple):
    exist = "No"
    if the_set:
        if the_tuple in the_set:
            exist = "Yes"
    return exist


def generate_report(kwd_path, okified_diffs=None, previous_report=None):
    in_k, in_d, in_both, def_diff, kwd, dmd = compare_keywords(
        kwd_path, expected_diffs=okified_diffs
    )
    prev_in_kwd, prev_in_dmd, prev_in_both = None, None, None
    if previous_report is not None:
        prev_diffs = read_previous_report(previous_report)
        prev_in_kwd = prev_diffs.in_kwd
        prev_in_dmd = prev_diffs.in_dmd
        prev_in_both = prev_diffs.in_both

    body = ""

    body += R("h1", "Keywords in the keyword dictionary but NOT in the datamodel schemas")
    table = "<table>\n"
    table += "  <tr>\n"
    column_hdrs = ["Keyword", "Known", "Okified"]
    for col in column_hdrs:
        table += f"    <th>{col}</th>\n"
    table += "  </tr>\n"

    for k in sorted(in_k):
        kwd_details = R("details", R("summary", _keyword_to_str(k)) + _keyword_details(kwd, dmd, k))
        known = check_tuple_exist(prev_in_kwd, k)
        okified = check_tuple_exist(okified_diffs, k)
        row = [kwd_details, known, okified]
        table += "  <tr>\n"
        for col_row in row:
            table += f"    <td>{col_row}</td>\n"
        table += "  </tr>\n"
    table += "</table>"
    body += table

    body += R("h1", "Keywords in the datamodel schemas but NOT in the keyword dictionary")
    table = "<table>\n"
    table += "  <tr>\n"
    column_hdrs = ["Keyword", "Known", "Okified"]
    for col in column_hdrs:
        table += f"    <th>{col}</th>\n"
    table += "  </tr>\n"

    for k in sorted(in_d):
        kwd_details = R("details", R("summary", _keyword_to_str(k)) + _keyword_details(kwd, dmd, k))
        known = check_tuple_exist(prev_in_dmd, k)
        okified = check_tuple_exist(okified_diffs, k)
        row = [kwd_details, known, okified]
        table += "  <tr>\n"
        for col_row in row:
            table += f"    <td>{col_row}</td>\n"
        table += "  </tr>\n"
    table += "</table>"
    body += table

    body += R("h1", "Keywords in both with definition differences")
    table = "<table>\n"
    table += "  <tr>\n"
    column_hdrs = ["Keyword", "Known", "Okified"]
    for col in column_hdrs:
        table += f"    <th>{col}</th>\n"
    table += "  </tr>\n"

    for k in sorted(def_diff):
        kwd_details = R(
            "details", R("summary", _keyword_to_str(k)) + _def_diff_details(def_diff[k])
        )
        known = check_tuple_exist(prev_in_both, k)
        okified = check_tuple_exist(okified_diffs, k)
        row = [kwd_details, known, okified]
        table += "  <tr>\n"
        for col_row in row:
            table += f"    <td>{col_row}</td>\n"
        table += "  </tr>\n"
    table += "</table>"
    body += table

    return R("html", R("body", body))


def _configure_cmdline_parser():
    parser = argparse.ArgumentParser(
        prog="kwtool",
        description="Generate a report of FITS keyword differences between "
        "datamodel schemas and the keyword dictionary",
    )
    parser.add_argument(
        "keyword_dictionary_path",
        help="Path to keyword dictionary directory.",
    )
    parser.add_argument(
        "-d",
        "--okified_diffs",
        default=None,
        help="Reviewed and accepted differences between datamodel schemas and the keyword dictionary.",
    )
    parser.add_argument(
        "-p",
        "--previous_report",
        default=None,
        help="Previous report of differences between datamodel schemas and the keyword dictionary.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        default="report.html",
        help="HTML report output filename.",
    )
    return parser


def _from_cmdline():
    # used in parent module __main__
    parser = _configure_cmdline_parser()
    args = parser.parse_args()
    if args.okified_diffs is not None:
        okd = open(args.okified_diffs, "r")
    else:
        okd = None

    report = generate_report(
        args.keyword_dictionary_path, okified_diffs=okd, previous_report=args.previous_report
    )

    if args.okified_diffs is not None:
        okd.close()

    with open(args.output_file, "w") as f:
        f.write(report)
