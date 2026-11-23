# Your shop data (CSV files)

Every `.csv` file in this folder becomes one table (file name = table name):

    distribution_centers.csv   events.csv   inventory_items.csv
    order_items.csv            orders.csv   products.csv   users.csv

The app builds `data/shop.db` from these files the first time it starts
(takes a few minutes for the full dataset). To load new data, replace the
files, delete `data/shop.db` and start the app again.

Docker mounts this folder read-only, so the app can never change your files.
`ecommerce-data-description.docx` describes every column.
Files in this folder are git-ignored, so your data is never committed.
