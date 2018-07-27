from ..data import _IdStore
import pygments
from pygments.formatters import HtmlFormatter, TerminalFormatter
import collections
import attr
import shutil
import pathlib
from jinja2 import Template
import json


@attr.s(slots=True, frozen=True, hash=True)
class Fragment:
    content = attr.ib()
    spans = attr.ib(default=attr.Factory(tuple), convert=tuple)


def render(submission_groups, dest="html"):
    src = pathlib.Path(__file__).absolute().parent
    dest = pathlib.Path(dest)
    dest.mkdir(exist_ok=True)

    # Copy compare50.js & compare50.css
    shutil.copyfile(src / "static/compare50.js", dest / "compare50.js")
    shutil.copyfile(src / "static/compare50.css", dest / "compare50.css")

    # formatter = HtmlFormatter(linenos=True)

    # with open(dest / "compare50.css", "a") as f:
        # f.write(formatter.get_style_defs('.highlight'))

    for match_id, (sub_a, sub_b, groups) in enumerate(submission_groups):
        frag_ids = _IdStore()
        span_ids = _IdStore()
        group_ids = _IdStore()

        span_to_group = {}
        file_to_spans = collections.defaultdict(list)
        group_to_spans = collections.defaultdict(list)
        span_to_fragments = collections.defaultdict(list)


        for group in groups:
            group_id = group_ids.id(group)
            group_to_spans[group_id] = [span_ids.id(span) for span in group.spans]
            for span in group.spans:
                file_to_spans[span.file].append(span)

        submissions = []
        for submission in (sub_a, sub_b):
            file_list = []
            for file in submission.files():
                frag_list = []
                for fragment in fragmentize(file, file_to_spans[file]):
                    frag_id = f"frag{frag_ids.id(fragment)}"
                    frag_list.append((frag_id, fragment.content))
                    for span in fragment.spans:
                        span_to_fragments[span_ids.id(span)].append(frag_id)
                file_list.append((str(file.name), frag_list))
            submissions.append((str(submission.path), file_list))

        # Get template
        with open(pathlib.Path(__file__).absolute().parent / "templates/match.html") as f:
            content = f.read()
        template = Template(content)
        # Render
        rendered_html = template.render(span_to_fragments=span_to_fragments, group_to_spans=group_to_spans, sub_a=submissions[0], sub_b=submissions[1])

        with open(dest / f"match_{match_id}.html", "w") as f:
            f.write(rendered_html)

def render_file_terminal(file, fragments, span_to_group):
    formatter = TerminalFormatter(linenos=True, bg="dark")
    print("*" * 80)
    print(file.name)
    print("*" * 80)
    for fragment in fragments:
        groups = list({span_to_group[span] for span in fragment.spans})
        print(pygments.highlight(fragment.content, file.lexer(), formatter))
        print("Spans:", fragment.spans)
        print("Number of groups:", len(groups))
        print("Matches with:", [group.spans for group in groups])
        print("=" * 80)


def fragmentize(file, spans):
    slicer = _FragmentSlicer()
    for span in spans:
        slicer.add_span(span)
    return slicer.slice(file)


class _FragmentSlicer:
    def __init__(self):
        self._slicing_marks = set()
        self._start_to_spans = collections.defaultdict(set)
        self._end_to_spans = collections.defaultdict(set)

    def slice(self, file):
        # Slicing at 0 has no effect, so remove
        self._slicing_marks.discard(0)

        # Perform slicing in order
        slicing_marks = sorted(self._slicing_marks)

        # Create list of spans at every fragment
        spans = [self._start_to_spans[0] - self._end_to_spans[0]]
        for mark in slicing_marks:
            cur = set(spans[-1])
            cur |= self._start_to_spans[mark]
            cur -= self._end_to_spans[mark]
            spans.append(cur)

        # Get file content
        with open(file.path) as f:
            content = f.read()

        # Make sure that last slice ends at the last index in file
        if slicing_marks and slicing_marks[-1] < len(content):
            slicing_marks.append(len(content))

        # Split fragments from file
        fragments = []
        start_mark = 0
        for fragment_spans, mark in zip(spans, slicing_marks):
            fragments.append(Fragment(content[start_mark:mark], fragment_spans))
            start_mark = mark

        return fragments

    def add_span(self, span):
        self._slicing_marks.add(span.start)
        self._slicing_marks.add(span.end)
        self._start_to_spans[span.start].add(span)
        self._end_to_spans[span.end].add(span)



#
#     return
#
#     dest = pathlib.Path(dest)
#
#     if not dest.exists():
#         os.mkdir(dest)
#
#     subs_to_groups = collections.defaultdict(list)
#
#     for group in groups:
#         subs_to_groups[(group.sub_a, group.sub_b)].append(group)
#
#     subs_groups = [(sm.sub_a, sm.sub_b, subs_to_groups[(sm.sub_a, sm.sub_b)]) for sm in submission_matches]
#
#     formatter = HtmlFormatter(linenos=True)
#
#     with open(dest / "style.css", "w") as f:
#         f.write(formatter.get_style_defs('.highlight'))
#
#     for i, (sub_a, sub_b, groups) in enumerate(subs_groups):
#         with open(dest / "match_{}.html".format(i), "w") as f:
#             f.write('<link rel="stylesheet" type="text/css" href="{}">'.format("style.css"))
#             f.write("{} {}<br/>".format(sub_a.path, sub_b.path))
#
#             for group in groups:
#                 f.write(" ".join(str(span) for span in group.spans))
#                 f.write("<br/>")
#
#             for html in mark_matches(sub_a, sub_b, groups, formatter):
#                 f.write(html)
#
#             # for sub in (sub_a, sub_b):
#             #     for file in sub.files():
#             #         with open(file.path) as in_file:
#             #             f.write(mark_matches(in_file.read(), formatter, file.lexer()))
#
# def mark_matches(sub_a, sub_b, groups, formatter):
#     htmls = []
#     for file in sub_a.files():
#         file_spans = [span for group in groups for span in group.spans if span.file.id == file.id]
#         with open(file.path) as f:
#             highlighted_html = pygments.highlight(f.read(), file.lexer(), formatter)
#
#         soup = BeautifulSoup(highlighted_html, 'html.parser')
#         for s in soup.find_all("span"):
#             print(dir(s))
#             print(s.contents)
#
#         htmls.append(str(soup))
#
#     return htmls