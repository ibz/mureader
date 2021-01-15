docker stop mureader
docker container rm mureader
docker run -d -e VIRTUAL_HOST=mureader.1984.solutions --network=webproxy --name=mureader -e LETSENCRYPT_HOST=mureader.1984.solutions -e LETSENCRYPT_EMAIL=mureader@1984.solutions -v $(pwd)/db:/db -v $(pwd)/instance-docker:/instance ibz0/mureader
