# zoialib

Command line librarian for Empress ZOIA patches


## Notes

A file name looks like this:

    021_zoia_Total_Random-680042cc3340b.bin
    ^^^      ^^^^^^^^^^^^ ^^^^^^^^^^^^^
    number        name   optional commit ID

We will store them without the `023_zoai` prefix.

    zoialib rename FILE [FILE...]


Defs:

* full patch name
* short patch name
* zdir - a zoia directory with files with full patch names


Renames all files to get rid of the prefix and recreate them when writing a zdir

We want to remember slot assignments. A file called slot_list.toml contains all the slots
assignments that have ever been seen, a map from slots to assignments. Because
many patches may want to go into the same slot, these assignments are ordered.
