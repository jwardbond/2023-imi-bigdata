# 2023 IMI BIGDataAIHUB Case Competition
*[Alexandre Granzer-Guay](https://github.com/alexandregranzerguay), [Jesse Ward-Bond](https://always-learn.com/), [Muhammad Maaz](http://mmaaz.ca/index.html)*

Repository here: https://github.com/jwardbond/2023-imi-bigdata

This repository contains our submission for the [2023-2024 IMI BIGDataAIHUB Case Competition](https://www.utm.utoronto.ca/bigdataaihub/events/fifth-annual-2023-2024-imi-bigdataaihub-big-data-and-artificial-intelligence-competition). In this competition we were given synthetic bank transaction data (emts, wire transfers, cash transactions, and customer data) and given three tasks: 
1. **Build a simple classifier** to flag high risk customers (money laundering)
2. **Identify wildlife trafficking networks** in the data using graph-based techniques
3. **Scrape trafficker names** from online sources match them with our data. 

We've completed all of these tasks, and our approaches to each of the - and the **webapp GUI** we developed to explore our results -  are contained in the respective folders within this repository.

## Setup
1. If you don't have jupyter installed already, follow [this guide](https://jupyter.org/install)
2. `pip install -r reqs_webapp.txt` if you just want to run the GUI **OR**  `pip install -r reqs_full.txt` to include dependencies for running the notebooks.

## Running the webapp
1. Install the requirements above.
1. Navigate to the webapp folder: `cd .\webapp\`
2. Launch the flask server using `python app.py`. 
    - It will take around 20 seconds for the server to construct the graph.
3. Type `localhost:5000` in your web browser or click [here](http://127.0.0.1:5000/)
   
For additional information, consult the README.md within the `.\webapp\` folder.

## Running the notebooks
- All notebooks should be run top-to-bottom, in the order they are stored presented in their respective folders
- We have cached all results, but if for some reason you want to re-run *everything*, it would be best to run the tasks in the following order: task_3 > task_2 > task_1
- The notebooks are well-documented, so README's are not provided within `.\task_1\` etc.