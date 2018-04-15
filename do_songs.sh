ROOT=D:/Dropbox/Public
TMP=chord/songs
cp -u $ROOT/Chords/Raw/*.cho chord/songs/
cd $TMP/
rm *.ps
cd -
python.exe make_songs.py chord/songs/
#cp -u $TMP/*.pdf $ROOT/Chords/
#cp -u $TMP/*.ppt $ROOT/Chords/
