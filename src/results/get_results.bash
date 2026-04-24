# Get all collection names and loop through them
for collection in $(mongosh user_study_test --quiet --eval "db.getCollectionNames().join(' ')"); do
    mongoexport --db=user_study_test --collection=$collection --out=$collection.json
done
