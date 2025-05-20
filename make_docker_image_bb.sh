#!/bin/bash
# dbca branch must be checked out and up to date in local work dir
date_var=$(date +%Y.%m.%d.%H.%M%S)
BUILD_TAG=dbcawa/disturbance:v$date_var
cd disturbance/frontend/disturbance/ &&

# Apply front end venv if it exists
{ 
    source venv/bin/activate && npm run build 
} || 
{ 
    npm run build
    echo "INFO: Front end built without venv"
}

#npm run build &&
cd ../../../ &&
docker image build --no-cache --tag $BUILD_TAG . &&
echo $BUILD_TAG &&
docker push $BUILD_TAG

