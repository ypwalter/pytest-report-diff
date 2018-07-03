"""Pytest HTML Report Diff 1.0

Usage:
  main.py (-h | --help)
  main.py (-v | --version)
  main.py [--previous=<str>] [--new=<str>] [--output=<str>]

Options:
  -h --help            Show this screen.
  -v --version         Show version.
  -p --previous=<str>  Set filename of your previous report.
  -n --new=<str>       Set filename of your new report.
  -o --output=<str>    Set filename of your output report [default: output.html].

"""
import re
from docopt import docopt
from lxml.cssselect import CSSSelector

# lxml special import magic
try:
  from lxml import etree
  # print("Running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    # print("Running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      # print("Running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        # print("Running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          # print("Running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")

class TestResults():
    __get_passed_row = CSSSelector('tr.passed.results-table-row')
    __get_failed_row = CSSSelector('tr.failed.results-table-row')
    __get_skipped_row = CSSSelector('tr.skipped.results-table-row')
    __get_error_row = CSSSelector('tr.error.results-table-row')
    __get_name = CSSSelector('td.col-name')

    def __init__(self, tree):
        # get cases nodes
        self.__passed_cases = self.__get_passed_row(tree)
        self.__failed_cases = self.__get_failed_row(tree)
        self.__skipped_cases = self.__get_skipped_row(tree)
        self.__error_cases = self.__get_error_row(tree)

    def count(self, type):
        if type == "passed":
            return len(self.__passed_cases)
        elif type == "failed":
            return len(self.__failed_cases)
        elif type == "skipped":
            return len(self.__skipped_cases)
        elif type == "error":
            return len(self.__error_cases)
        else:
            return -1

    def get_list(self, type):
        if type == "passed":
            data = self.__passed_cases
        elif type == "failed":
            data = self.__failed_cases
        elif type == "skipped":
            data = self.__skipped_cases
        elif type == "error":
            data = self.__error_cases
        else:
            return []

        ret = []
        for item in data:
            l = [re.sub(r'http\S+[^];]', '', x) for x in self.__get_name(item)[0].text.strip().split("::")[0:4] if x != "()" and not x.startswith("Test")]
            ret.append(" ".join(l))
        return ret

class DiffResults():
    # passed[0]: Used to "PASS", passed[1]: "PASS" now
    __passed = [[], []]
    __failed = [[], []]
    __skipped = [[], []]
    __error = [[], []]

    #tree1 should be the older result, tree2 should be the new result
    def __init__(self, test_results1, test_results2):
        self.__passed[0] = diff(test_results1.get_list("passed"), test_results2.get_list("passed"))
        self.__passed[1] = diff(test_results2.get_list("passed"), test_results1.get_list("passed"))
        self.__failed[0] = diff(test_results1.get_list("failed"), test_results2.get_list("failed"))
        self.__failed[1] = diff(test_results2.get_list("failed"), test_results1.get_list("failed"))
        self.__skipped[0] = diff(test_results1.get_list("skipped"), test_results2.get_list("skipped"))
        self.__skipped[1] = diff(test_results2.get_list("skipped"), test_results1.get_list("skipped"))
        self.__error[0] = diff(test_results1.get_list("error"), test_results2.get_list("error"))
        self.__error[1] = diff(test_results2.get_list("error"), test_results1.get_list("error"))

    def return_previously_passed(self):
        return self.__passed[0]

    def return_newly_passed(self):
        return self.__passed[1]

    def return_previously_failed(self):
        return self.__failed[0]

    def return_newly_failed(self):
        return self.__failed[1]

    def return_previously_skipped(self):
        return self.__skipped[0]

    def return_newly_skipped(self):
        return self.__skipped[1]

    def return_previously_error(self):
        return self.__skipped[0]

    def return_newly_error(self):
        return self.__skipped[1]

# return difference of two list
def diff(li1, li2):
    return (list(set(li1) - set(li2)))

# function to remove script and style tag
def stripTags(text):
    # scripts = re.compile(r'<script.*?/script>')
    scripts = re.compile(r'<(script).*?</\1>(?s)')
    css = re.compile(r'<style.*?/style>')

    text = scripts.sub('', text)
    text = css.sub('', text)
    text = text.replace("", "")
    text = text.replace("", "")
    return text

# read and return the lxml object tree
def returnTree(filename):
    # read data from file
    with open(filename, "r") as f:
        data_list = f.readlines()
        data = "".join(data_list)

    # remove data that could be harmful to lxml
    data = stripTags(data)

    with open("temp", "w") as f:
        f.write(data)

    # get a lxml object
    tree = etree.fromstring(data)
    return tree

# generate HTML Table accordingly
def generateTable(ipt, text):
    start = "<table id=\"" + text.replace(" ", "") + "\" class=\"table\"><tr><th>" + text + "</th></tr>"
    end = "</table>"
    content = ""

    ipt.sort()
    for i in ipt:
        content += "<tr><td>" + i + "</td></tr>"

    return start + content + end

# generate HTML in designated format
def generateHTML(p, f, e):
    start = "<html><head><link rel=\"stylesheet\" href=\"styles.css\"><body>"
    end = "</body></html>"
    content = ""
    content += generateTable(f, "Newly Failed")
    content += generateTable(p, "Newly Passed")
    content += generateTable(e, "Newly Errored")
    HTML = start + content + end
    HTML = HTML.replace("<script>", "script")
    HTML = HTML.replace("</script>", "/script")

    return HTML

# this is the main function for diff two report
def main():
    arguments = docopt(__doc__)

    file1, file2, output_file = arguments["--previous"], arguments["--new"], arguments["--output"]
    tree1 = returnTree(file1)
    tree2 = returnTree(file2)

    # get test results object for each html file
    test_results1, test_results2 = TestResults(tree1), TestResults(tree2)

    # get the diff object for 2 files
    dr =  DiffResults(test_results2, test_results1)

    # get newly failed test cases (more to choose from DiffResults class)
    # TODO: change this to output html later
    new_pass = dr.return_newly_passed()
    new_failure = dr.return_newly_failed()
    new_error = dr.return_newly_error()
    HTML = generateHTML(new_pass, new_failure, new_error)
    with open(output_file, "w") as f:
        f.write(HTML)

if __name__ == "__main__":
    main()
