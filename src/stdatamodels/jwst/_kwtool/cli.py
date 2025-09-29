import argparse
from datetime import date
from html.parser import HTMLParser
from pprint import pformat

from stdatamodels.jwst._kwtool.compare import print_dict_to_file
from stdatamodels.jwst._kwtool.okified_diffs import okifeid_expected_diffs

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
        elif "Keywords in previous report not present" in data:
            self.save_in_kwd = False
            self.save_in_dmd = False
            self.save_in_both = True

        if "HDU:" in data:
            items = data.split(sep="KEYWORD:")
            hdu = items[0].replace("HDU:", "").strip()
            keywd = items[-1].strip()
            if self.save_in_kwd:
                self.in_kwd.append((hdu, keywd))
            elif self.save_in_dmd:
                self.in_dmd.append((hdu, keywd))
            elif self.save_in_both:
                self.in_both.append((hdu, keywd))


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


def _check_tuple_exist(the_set, the_tuple):
    exist = "No"
    if the_set:
        if the_tuple in the_set:
            exist = "Yes"
    return exist


def _check_keyword_exist(the_set, the_tuple):
    exist = "No"
    if the_set:
        for tpl in the_set:
            if tpl[1] == the_tuple[1]:
                exist = "Yes"
    return exist


def _loop_check_keyword_exist(set1, set2, set3, set4):
    removed_tuples = []
    for tpl in set1:
        existin2 = _check_keyword_exist(set2, tpl)
        if existin2 == "No":
            existin3 = _check_keyword_exist(set3, tpl)
            if existin3 == "No":
                existin4 = _check_keyword_exist(set4, tpl)
                if existin4 == "No":
                    removed_tuples.append(tpl)
    return removed_tuples


def _check_removed_keywords(prev_diffs, in_k, in_d, in_both):
    prev_in_kwd = prev_diffs.in_kwd
    prev_in_dmd = prev_diffs.in_dmd
    prev_in_both = prev_diffs.in_both
    removed_in_kwd = _loop_check_keyword_exist(prev_in_kwd, in_k, in_d, in_both)
    removed_in_dmd = _loop_check_keyword_exist(prev_in_dmd, in_k, in_d, in_both)
    removed_in_both = _loop_check_keyword_exist(prev_in_both, in_k, in_d, in_both)
    removed_keywords = []
    if len(removed_in_kwd) > 0:
        for tpl in removed_in_kwd:
            removed_keywords.append(tpl + ("Keyword_dictionary",))
    if len(removed_in_dmd) > 0:
        for tpl in removed_in_dmd:
            removed_keywords.append(tpl + ("Datamodels",))
    if len(removed_in_both) > 0:
        for tpl in removed_in_both:
            removed_keywords.append(tpl + ("Both",))
    return removed_keywords


def generate_report(kwd_path, okified_diffs=None, previous_report=None):
    in_k, in_d, in_both, def_diff, kwd, dmd = compare_keywords(
        kwd_path, expected_diffs=okified_diffs
    )
    # save the keywords for the current run
    print_dict_to_file("def_diff", def_diff, "def_diff.py")

    # get all the keywords from the previous report
    prev_in_kwd, prev_in_dmd, prev_in_both = None, None, None
    if previous_report is not None:
        prev_diffs = read_previous_report(previous_report)
        prev_in_kwd = prev_diffs.in_kwd
        prev_in_dmd = prev_diffs.in_dmd
        prev_in_both = prev_diffs.in_both
        # check if any keyword from previous report is missing in this round
        removed_keywords = _check_removed_keywords(prev_diffs, in_k, in_d, in_both)
    else:
        removed_keywords = [("N/A", "N/A", "N/A")]

    body = ""

    # Add header info
    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    stdatamodels_tag = "4.0.1"
    jwstkw_tag = "JWSTDP-2025.3.1-3"
    tags = "Tags used: stdatamodels=" + stdatamodels_tag + " ,  jwstkw=" + jwstkw_tag
    body += R("h1", "Date: " + str(formatted_date))
    body += R("h1", tags)

    body += R("h1", "Keywords in the keyword dictionary but NOT in the datamodel schemas")
    table = "<table>\n"
    table += "  <tr>\n"
    column_hdrs = ["Keyword", "Known", "Okified"]
    for col in column_hdrs:
        table += f"    <th>{col}</th>\n"
    table += "  </tr>\n"

    for k in sorted(in_k):
        kwd_details = R("details", R("summary", _keyword_to_str(k)) + _keyword_details(kwd, dmd, k))
        known = _check_tuple_exist(prev_in_kwd, k)
        okified = _check_tuple_exist(okified_diffs, k)
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
        known = _check_tuple_exist(prev_in_dmd, k)
        okified = _check_tuple_exist(okified_diffs, k)
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
        known = _check_tuple_exist(prev_in_both, k)
        okified = _check_tuple_exist(okified_diffs, k)
        row = [kwd_details, known, okified]
        table += "  <tr>\n"
        for col_row in row:
            table += f"    <td>{col_row}</td>\n"
        table += "  </tr>\n"
    table += "</table>"
    body += table

    body += R("h1", "Keywords in previous report not present in this run")
    table = "<table>\n"
    table += "  <tr>\n"
    column_hdrs = ["Keyword", "Previous_report_section"]
    for col in column_hdrs:
        table += f"    <th>{col}</th>\n"
    table += "  </tr>\n"

    if len(removed_keywords) > 0:
        for tpl in sorted(removed_keywords):
            k = (tpl[0], tpl[1])
            rmvd_from = tpl[2]
            kwd_details = R("summary", _keyword_to_str(k))
            row = [kwd_details, rmvd_from]
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
        action="store_true",
        default=False,
        help="Use reviewed and accepted differences (okified_diffs file) between datamodel "
        "schemas and the keyword dictionary.",
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
    if args.okified_diffs:
        okd = okifeid_expected_diffs
    else:
        okd = None

    report = generate_report(
        args.keyword_dictionary_path, okified_diffs=okd, previous_report=args.previous_report
    )

    with open(args.output_file, "w") as f:
        f.write(report)
