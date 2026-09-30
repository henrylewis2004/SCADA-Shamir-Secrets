python ./src/prep/file_maker.py
echo $?
docker compose up --build --abort-on-container-exit
echo $?
