fstests_result_webui
====================

About
-----

This is a tool to generate static pages of one or more fstests runs.

Usage
-----

```
./generate.py <result.xml> [-D <output_dir>]
```

**result.xml** is generate by utilizing fstests xunit report facility.
This can be done by the following command:

```
# cd fstests
# ./check -R xunit
```

If no **output_dir** is specified,, current directory will be used.

For now, users still have to do the following works by themselves:

- Run fstests

- Copy the **result.xml** to the host

Output directory hierarchy
--------------------------

The hierarchy of **output_dir** would look like this:

```
.
|- index.html                   # The summary page of all runs
|- details/
   |- <hostname>/               # The hostname from each xml
      |- <section>/             # The section name of the run (default is "global")
         |- <timestamp>/        # Timestamp of the run, ISO 8601, to seconds.
            |- index.html       # Summary of the specific run
            |- <seqnum.dmesg>   # Saved dmesg
            |- <seqnum.out.bad> # Failed output
```

One example would look like this:

```
.
|- index.html
|- details/
   |- btrfs-rock5b/
   |  |- global/
   |     |- 2022-12-19T18:25:12/
   |     |  |- index.html
   |     |  |- 011.out.bad
   |     |  |- 011.dmesg
   |     |- 2022-12-19T18:32:50/
   |        |- index.html
   |- btrfs-rk3399/
      |- global/
         |- 022-12-16T14:57:06/
            |- index.html
```
