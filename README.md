# Porter County Property Parcel Parser

The Porter County Indiana [Property Tax Assessment](http://www.xsoftin.com/porter/) website
has limited searching/filtering functionality.
This script scrapes it
and pulls out the only the parcels
with a `Property Class` of `exempt`
and whose `Property Class` is `685`.

More flexible filtering is possible,
but it's probably YAGNI.

## Usage

	$ pip install -r requirements.txt
	$ python pcppp.py

Then sit back,
relax,
and watch things starting popping up
in the `results/` folder.

## Progress-Saving

Progress is saved in a json file
in the results folder.
If things crash,
it will use that file to avoid re-parsing
parcels that have already finished.
If you'd like to restart everything,
just delete the `results/` folder.

## Credit

And for the record,
this script counts as a Christmas present
to the person who would otherwise
have had to sort through 272 pages manually.
You know who you are,
person,
and expect payment in kisses.
