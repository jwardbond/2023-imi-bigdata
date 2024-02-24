# Wildlife Trafficking Webapp

## Running the webapp
1. Navigate to the webapp folder: `cd .\webapp\`
2. Launch the flask server using `python app.py`. 
    - It will take around 20 seconds for the server to construct the graph.
3. Open index.html in a web-browser, or your favourite live server. 
    - The table and large graphs take a second to render.

## Playing with the GUI
The main table is default sorted by suspicion score, so you can see the most suspicious people at the top. You can do all sorts of things with it:
- search, filter, sort columns
- single click on a table row and their transaction graph will appear
- double click on a table row and their customer information page will open

In the transaction graph, the silver node is the customer you clicked. The bank is the green node, customers are blue nodes, and external people are red nodes. When looking at the transaction graph, you can:
- hover over a node to see who they are: their customer ID, name, or, if they are external, their country of origin
- hover over an edge to see what type of transaction it was and the amount
- select and drag nodes to rearrange the graph, or zoom in, to see relationships more closely
- double click on a node to open their customer information page

On a customer's information page, you can see their KYC information, like their name and occupation. You can also see tables of all their transactions. Customers who they transacted with will have links on their names so you can further investigate them. You may also see red alert icons in front of some information. These refer to flags that our modelling thought was important. For example, if you see a red alert beside someoone's occupation, you can hover over it for more information as to why we thought it was suspicious. If you see a red alert beside someone's name, that means they may be a known trafficker. If you click on this icon, you will see an explanation and links to relevant sources we scraped from the internet.

These features make exploring suspicious customers and their networks very easy!


