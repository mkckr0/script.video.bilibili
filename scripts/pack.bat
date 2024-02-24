pushd "%~dp0..\.."

set id=script.video.bilibili

del %id%\out\%id%.zip
7z a -tzip "%id%\out\%id%.zip" "%id%" "-x@%id%\scripts\exclude.txt"

popd