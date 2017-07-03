from __future__ import print_function

import os
import subprocess
import sys

import six
import vagrant
import yaml


class FirstRunCIError(Exception):
    pass


class Configuration(object):
    def __init__(self):
        self.name = None
        self.url = None
        self.head = None
        self.has_submodules = None
        self.docs = None
        self.snippets = None
        self.scripts = None
        self.box = None

    def parse(self, path):
        doc = yaml.load(open(path))
        self.name = doc["name"]
        self.vagrant = vagrant.Vagrant(root=self.name)
        self.url = doc["git"]["url"]
        self.head = doc["git"]["head"]
        self.has_submodules = doc["git"].get("recursive", False)
        if isinstance(doc["docs"], six.string_types):
            self.docs = [doc["docs"]]
        else:
            self.docs = list(doc["docs"])
        self.snippets = []
        self.scripts = []
        for step in doc["steps"]:
            texts = step.get("text", [])
            if isinstance(texts, six.string_types):
                texts = [texts]
            self.snippets.extend(texts)
            scripts = step.get("script", [])
            if isinstance(scripts, six.string_types):
                scripts = [scripts]
            self.scripts.extend(scripts)
        self.box = doc["vagrant"]["box"]

    def run(self, destroy=True):
        self.get_source()
        self.ensure_vagrantfile()
        self.check_docs()
        self.vagrant_up()
        try:
            self.run_scripts()
        finally:
            if destroy:
                self.vagrant_destroy()

    def get_source(self):
        if os.path.isdir(self.name):
            args = ["git", "pull", "origin", self.head]
            if self.has_submodules:
                args.append("--recurse-submodules=on-demand")
            subprocess.check_call(args, cwd=self.name)
        else:
            args = ["git", "clone", self.url, "--branch", self.head,
                    self.name]
            if self.has_submodules:
                args.append("--recursive")
            subprocess.check_call(args)

    def ensure_vagrantfile(self):
        output = subprocess.check_output(["git", "ls-files", "--",
                                          "Vagrantfiles"],
                                         cwd=self.name)
        if len(output) == 0:
            exclude_path = os.path.join(self.name, ".git/info/exclude")
            exclude_f = open(exclude_path, "r")
            exclude_lines = exclude_f.readlines()
            exclude_f.close()
            if "/Vagrantfile\n" not in exclude_lines:
                exclude_f = open(exclude_path, "a")
                exclude_f.write("\n/Vagrantfile\n")
                exclude_f.close()
            vagrant_path = os.path.join(self.name, "Vagrantfile")
            vagrant_f = open(vagrant_path, "w")
            vagrant_f.write("Vagrant.configure(\"2\") do |config|\n"
                            "  config.vm.box = \"{}\"\n"
                            "end\n".format(self.box))
            vagrant_f.close()

    def check_docs(self):
        doc_contents = [open(os.path.join(self.name, doc_path), "r").read()
                        for doc_path in self.docs]
        for snippet in self.snippets:
            for text in doc_contents:
                if snippet in text:
                    break
            else:
                raise FirstRunCIError("The documentation text for a step "
                                      "has changed or is no longer present: "
                                      "{!r}".format(snippet))

    def vagrant_up(self):
        self.vagrant.up()

    def run_scripts(self):
        for script in self.scripts:
            self.vagrant.ssh(command=script)

    def vagrant_destroy(self):
        self.vagrant.destroy()


def main():
    try:
        configs = []
        destroy = True
        if len(sys.argv[1:]) == 0:
            print("Usage: {} config.yaml [...]".format(sys.argv[0]))
            sys.exit(1)
        for arg in sys.argv[1:]:
            if arg == "--no-destroy":
                destroy = False
            if not os.path.isfile(arg):
                raise FirstRunCIError("File {} does not exist".format(arg))
            config = Configuration()
            config.parse(arg)
            configs.append(config)
        for config in configs:
            config.run(destroy)
    except FirstRunCIError as e:
        print(e.args[0])
        sys.exit(1)
