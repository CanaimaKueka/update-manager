#!/bin/bash

rm -rf build dist

OUTFILE="po/POTFILES.in"

echo "Creating po/POTFILES.in"

echo "[encoding: UTF-8]" > $OUTFILE

PY_FILES=`find ./UpdateManager -name "*.py"`

for pyfile in $PY_FILES
do
    # Get rid of "./" reported by find.
    pyfile=${pyfile:2}
    echo "$pyfile" >> $OUTFILE
done

IN_FILES=`find . -name "*.in"`

for infile in $IN_FILES
do
    if [ "$infile" != "./po/POTFILES.in" -a "$infile" != "./MANIFEST.in" ]
    then
        # Get rid of "/." reported by find
	infile=${infile:2}
	echo "$infile" >> $OUTFILE
    fi
done

UI_FILES=`find ./data/ -name "*.ui"`

for uifile in $UI_FILES
do
    # Get rid of "./" reported by find
    uifile=${uifile:2}
    echo "$uifile" >> $OUTFILE
done


# Finally, add our script files.
echo "update-manager" >> $OUTFILE
echo "update-manager-text" >> $OUTFILE