# firstrunci

`firstrunci` automates the testing of developer-facing installation instructions.

## Overview

This repository provides a command line tool, `firstrunci`, that orchestrates testing a project's installation instructions. It requires a configuration file with metadata for the project, installation commands to run, and the corresponding documentation excerpts. `firstrunci` handles cloning the project, checking if the documentation excerpts are still present in the project, creating a Vagrantfile when needed, and running the installation and test commands in a virtual machine using [Vagrant](https://vagrantup.com/).

## Installation

Python 3, Git, Vagrant, and VirtualBox 5.1  must be installed first. I recommend installing `firstrunci` and its Python dependencies in a virtualenv. To install, run `python3 setup.py install`.

VirtualBox cannot host 64-bit VMs when the host itself is running inside a hypervisor, so this cannot be run on most cloud computing services. VirtualBox 5.1 is required because it includes breaking changes to network configuration, and most Vagrant box definitions target VirtualBox 5.1 now.

## Usage

`firstrunci` takes any number of configuration files as command line arguments. It will test each in turn.

Example:

```bash
firstrunci oversight.garden.yaml openelections.yaml
```

By default, all Vagrant VMs will be cleaned up after testing is complete. If you would like to override this and keep the VMs for further inspection, pass `--no-destroy` as a command line argument.

The projects will be cloned in directories next to the configuration files. On subsequent runs, `git clean -dfx` will be run in the directory, so do not store any unsaved work there.

The [divergentdave/firstrunci-config](https://github.com/divergentdave/firstrunci-config) repository contains several ready-made configuration files. (and is open for more)

## Configuration file format

Configuration files should contain a single YAML document, where the top level object is a mapping with the following keys:

### name

The value for `name` is used as a directory name for the local clone of the project under test. As such, this name should be unique and safe for file systems.

Example:

```yaml
name: my-project
```

### git

The value for the `git` key should be another mapping, under which the value for `url` should be the Git URL to clone the project from, and the value for `head` should be the name of the branch or commit to check out. If a repository has submodules, add `recursive: true` to the `git` mapping.

Example:

```yaml
git:
    url: "http://example.com/path/name.git"
    head: mybranch
```

### vagrant

If a project has its own Vagrantfile already, this section is not needed, and will be ignored. Otherwise, the value should be a mapping with the sole key of `box`, where the value for `box` is the name of a Vagrant box to run the commands in.

Example:

```yaml
vagrant:
    box: bento/ubuntu-16.10
```

### docs

The value under `docs` should be one or more paths to the documentation files inside the project that will be monitored for changes. The value can be either a single string or a sequence of strings.

Examples:

```yaml
docs: README.md
```

```yaml
docs:
  - CONTRIBUTING.md
  - docs/setup.md
```

### steps

The value under `steps` should be a sequence of mappings, each of which constitutes a "step" in testing the installation process.

Each step may have one or both of `text` and `script` as keys. The values under either key may be a string or a sequence of strings. Each string under `text` is a snippet from the documentation to be monitored. If the corresponding part of the documentation is modified in the upstream project later, an error will be raised. Each string under `script` is a shell command to be run inside the VM. All commands are run from the `/vagrant` directory, i.e. the root of the project under test. Each command is run in a separate shell, so environment variables will not persist from one to the next. If any shell command returns a status code indicating a failure, then execution will stop there with an error. Note that strings containing colons or other YAML-relevant characters must be quoted, and backslashes in strings need to be doubled for proper escaping.

(The association between the text and the script in each step is solely for readability and maintainability. Internally, the documentation snippets and the shell commands are checked in two separate passes.)

Example:

```yaml
steps:
  - text: copy settings.ini.example to settings.ini
    script: cp settings.ini.example settings.ini
  - text: Ubuntu 16.10
  - text:
      - Install Python
      - Python 3
    script:
      - sudo apt-get update
      - sudo apt-get install -y python3
  - script: sudo service elasticsearch start
```
