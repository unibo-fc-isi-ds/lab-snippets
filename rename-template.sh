#!bash

NEW_NAME=$1

if [[ -z "$NEW_NAME" ]]; then
    echo "Must provide a new name as argument" 1>&2
    exit 1
fi

for FILE in `find . -type f  -not -iname '*.pyc' -not -path '*.git*'`; do 
    sed -i'.bak' -e "s/my_project/$NEW_NAME/g" $FILE
done

for FILE in `find .github -type f  -not -iname '*.pyc'`; do 
    sed -i'.bak' -e "s/my_project/$NEW_NAME/g" $FILE
done

mv my_project $NEW_NAME

rm .github/**/*.bak **/*.bak .*.bak *.bak *.sh
