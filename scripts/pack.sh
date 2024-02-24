#!/bin/bash

folder=$(realpath $(dirname $0)/..)
id=script.video.bilibili

pushd $folder/..

rm $id/out/$id.zip
mkdir $id/out
zip -r "$id/out/$id.zip" "$id" "-x@$id/scripts/exclude.txt"

popd