Does some counting, analysis, and visualization on the usage of commentfaces on CDF and the broader /r/anime.

Dependencies
----
* matplotlib - for visualizations
* pmaw - a wrapper around the pushshift api

Running
----
`python3 commentface_counting.py` - will save the graphic and output the raw and processed data to the terminal

`time python3 commentface_counting.py > all_cdf_results.txt` - will save the graphic, output the data into that file, and also time how long it took

Just change the datetime variable to change the amount of data collected.

Also providing a Dockerfile, but it's definitely not a "production" quality one lol.

`docker build -t commentface_counting .` - build the container

`docker build --pull --no-cache -t commentface_counting .` - build the container but with the latest security updates (will be slower cause we're not using the cache so only do this every now and again)

`docker run --rm -it -v $(pwd):/app commentface_counting /bin/bash` - makes the current directory (assumed to be the project directory) a shared volume with the container, which it dumps you into, where you can run the manual commands from above

`time docker run -v $(pwd):/app commentface_counting` - that volume stuff, but also it will save the graphic, output the data into the file, and time how long it took
