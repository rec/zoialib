# 🔊 `zoialib`: a patch librarian for ZOIA 🔊

## What is `zoialib`?

Inspired by the ground-breaking
[`repatch.py`](https://patchstorage.com/repatch-py-organize-and-auto-name-your-patches/)
([source](https://gist.github.com/BenQuigley/7b4c70cac1183a16aed89b8b209364a2)),
`zoialib` is a command line program that prepares patch directories to download
to ZOIA.

## How to install `zoialib`

You can use `pip`, `uv`, `poetry`, `conda` or any other tool for installing
Python modules.

```
pip install zoialib

# or

uv add zoialib

# or

poetry add zoialib

# or

conda install zoialib
```

## Some background on ZOIA patch directories

ZOIA patches are files, organized by name. Here's a ZOIA directory with
eight patches:

```
000_zoia_Gainfully_fun.bin
001_zoia_Rephrase_v1_0.bin
002_zoia_SAMPLE.bin
003_zoia_Always_On.bin
004_zoia_Angry_robots.bin
005_zoia_Elemental_Ring.bin
006_zoia_Loop_Noodle-680ef8977c75f.bin
007_zoia_Tiny_Orchestra.bin
```

The first three letters of a ZOIA patch file name are the _slot number_, three digits
like `096`.

The next six letters are the fixed _marker string_ `_zoia_`.

Then then there's the _patch name_, e.g. `Gainfully_fun`, and the patch file always ends
with the _suffix_ `.bin`.

Finally, patch slots must always be in consecutive order, with no gaps. If don't you want
any patch in a slot, you must fill it with
a blank patch [like these](https://patchstorage.com/64-blank-zoia-patches/).

## What problems does `zoialib` solve?

The slot number is part of the ZOIA patch file name, which is very convenient for
configuring ZOIA, but is clumsy and time-consuming if you have a lot of patches and you
only download some of them at a time to ZOIA.

`zoialib` assumes that only the _patch name_ determines what is in the patch, and
handles keeping track of the slots for you.

NOTE: if you have a setup where two files like, say, `000_zoia_synth.bin` and
`001_zoia_synth.bin` have the same patch name `synth` but are _different_ patches, **do
not use this program** as it might destroy your data!

## The commands

`zoialib` has two commands.

* `zoialib prepare` prepares a ZOIA patch directory
* `zoialib rename` renames patch files to remove the slot number and marker string

### `zoialib rename`

`zoialib rename FILE [FILE...]` simply renames one or more ZOIA patch files to just use
the patch name.

For example, `zoialib rename 004_zoia_Angry_robots.bin` would rename the file
`004_zoia_Angry_robots.bin` to `Angry_robots.bin`.

Very useful in bulk operations using a "glob", like `zoialib rename */*.bin`, but
remember that you could wreak havoc this way, so be careful.

### `zoialib prepare`

`zoialib prepare FILE [FILE...]` prepares ZOIA patch files into a ZOIA patch directory.

#### Basic example:

```
$ zoialib prepare --verbose downloads/000*.bin
Making output directory zoia-2025-09-28_12-30-41
Copying downloads/000_zoia_Gainfully_fun.bin to zoia-2025-09-28_12-30-41/000_zoia_Gainfully_fun.bin
Copying downloads/000_zoia_Rephrase_v1_0.bin to zoia-2025-09-28_12-30-41/001_zoia_Rephrase_v1_0.bin
Copying downloads/000_zoia_SAMPLE.bin to zoia-2025-09-28_12-30-41/002_zoia_SAMPLE.bin
3 files copied to zoia-2025-09-28_12-30-41
```

#### Slot assignment

You can put individual patches into a specific slot using `:`. If this generates gaps,
they get filled in with a blank patch:

```
$ zoialib prepare -v  --output=output downloads/one.bin:2 downloads/two.bin:1  downloads/three.bin:5

Making output directory output
Copying /Users/tom/code/zoialib/zoia_empty.bin to output/000_zoia_.bin
Copying downloads/two.bin:1 to output/001_zoia_Rephrase_v1_0.bin
Copying downloads/one.bin:2 to output/one.bin
Copying /Users/tom/code/zoialib/zoia_empty.bin to output/003_zoia_.bin
Copying /Users/tom/code/zoialib/zoia_empty.bin to output/004_zoia_.bin
Copying downloads/three.bin:5 to output/005_three.bin
```

#### The slot list file

If you like your slot numbers to remain stable, for example if you are sending program
changes to ZOIA, there's a nifty feature called the _slot list file_.  by default named
`slot_list.toml`, automatically created and maintained by `zoialib`.

Running `zoialib prepare` with the `--update-slots-file`/`-u` flag updates the slot list
file with the slot assignments from the current run so the next time these patches
are seeing, they can get the same patch number if possible.

```
$ zoialib prepare --update-slots-file -v -o output one.bin two.bin three.bin
Copying one.bin to output/000_zoia_one.bin
Copying two.bin to output/001_zoia_two.bin
Copying three.bin to output/002_zoia_three.bin

$ # Now it remembers the slots, like this:

$ zoialib prepare -v -o output three.bin one.bin two.bin
Copying one.bin to output/000_zoia_one.bin
Copying two.bin to output/001_zoia_two.bin
Copying three.bin to output/002_zoia_three.bin
```

The slot list file is in [TOML](https://toml.io/en/), a language for configuration files
that is designed to be easy for people to edit without making mistakes.

## Useful features common to both commands

### Flags

* `--help` or `-h` prints the help message for the command
  * Example: `zoialib rename --help` or `zoialib rename -h`.

* `--verbose`/`-v` makes the program print more information

* `--dry-run`/`-d` turns on `--verbose`, but doesn't actually execute the commands

### Text files containing patch file names

Instead of typing individual patch names, you can also use text files, ending in `.txt`,
where each line is a patch file name or another text file.

Blank lines and everything after the `#` comment character are ignored. Wildcard "globs"
`*`, `?`, `[` and `]`, are expanded.

Example:

```
$ cat my-patches.txt

# For Friday's show

downloads/one.bin:2
downloads/two.bin:1  @ I hate this patch.

# downloads/seventeen.bin:17
downloads/three.bin:5

$ zoialib prepare -v -o=output my-patches.txt

Copying /Users/tom/code/zoialib/zoia_empty.bin to output/000_zoia_.bin
Copying downloads/two.bin:1 to output/001_zoia_Rephrase_v1_0.bin
Copying downloads/one.bin:2 to output/one.bin
Copying /Users/tom/code/zoialib/zoia_empty.bin to output/003_zoia_.bin
Copying /Users/tom/code/zoialib/zoia_empty.bin to output/004_zoia_.bin
Copying downloads/three.bin:5 to output/005_three.bin

```
