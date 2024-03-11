from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
import requests
from requests import session
import psycopg2
import logging
from dotenv import load_dotenv
import os

# load .env
load_dotenv()

# Set up logging
logging.basicConfig(filename=os.getenv("LOG_FILE"), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to the PostgreSQL database:
try:
	conn = psycopg2.connect(
		dbname=os.getenv("DB_NAME"),
		user=os.getenv("DB_USER"),
		password=os.getenv("DB_PASSWORD"),
		host=os.getenv("HOST"),
		port=os.getenv("PORT")
	)
	logging.info("Connected to the database successfully.")

except psycopg2.Error as e:
	logging.error(f"Unable to establish connection with the database! {e}")
	cur.close()
	conn.close()
	raise SystemExit

# Create cursor object:
cur = conn.cursor()

# Construct SQL INSERT statement
insert_statement = f"""
    INSERT INTO tbllinks (title, url)
    VALUES (%s, %s)
"""

index = 0 # index - for following the items downstream
maxitem = 0 # maxitem - for holding an account of the maxitem, for later calculation

# Obtain MAXITEM of HN
try:
	index = requests.get("https://hacker-news.firebaseio.com/v0/maxitem.json").json() 
	maxitem = index
	logging.info(f"Got last item successfully: MAXITEM = {index}")
except requests.exceptions.RequestsException as e:
	logging.error(f"Could not get max item! Aborting with Exception: {e}")
	cur.close()
	conn.close()
	raise SystemExit

# Initialize:

item_limit = 0 # last item
item_batch_size = 1000 # items per commit

insert_global_count = 0 # total inserts count
insert_local_count = 0 # inserts in the current commit count
commit = 1 # commit count
p_item = 0 # processed items count

response = []
futures = []


# Try to send requests
# Starting from the last Item, down to the bottom (item: 0)
# Every request, execution, insert, etc. is subject to an exception as the scrape process can be unreliable

p_item = index - item_batch_size +1 # Record starting item 
ss = session()
try:
	while index>item_limit: 

		try:
			with FuturesSession(session = ss) as session: # Utilizing FuturesSessions to hold a bunch of requests to do at once

				try:
					futures = [session.get(f"https://hacker-news.firebaseio.com/v0/item/{_}.json") for _ in range(index - item_batch_size+1, index+1)]
				except Exception as e:
					logging.error(f"SGETFAIL on item between: {index-item_batch_size} and: {index} SKIPBATCH Exception: {e}")

				for future in as_completed(futures):

					response = future.result().json()

					if "url" in response and "title" in response: # verify it is a story/show_hn

						try:
							cur.execute(insert_statement, (response["title"],response["url"]))
							insert_local_count +=1
							logging.info(f"INSSUCCESS statement item: ({index}) execution successful")
						except psycopg2.Error as e:
							logging.error(f"INSFAIL statement item: ({index}) excecution FAILED with exception: {e}")

					index -= 1 # Item processed mandates going to the next one. Top to bottom.

			
		except Exception as e: # Error with variables or concurrent results

			logging.error(f"PARSEFAIL on item between: {index-item_batch_size} and: {index} SKIPBATCH ROLLBACK Exception: {e}") 
			conn.rollback() # rollback to reset hanged transactions
			insert_local_count = 0
			index -= item_batch_size -1 # skip the batch


		# Commit changes:
		try: 
			conn.commit()
			p_item = index - item_batch_size +1 # Record starting item 

			insert_global_count +=insert_local_count
			logging.info(f"Commit number: {commit} successful. item processed: {maxitem-index} Inserted items count: {insert_global_count} ")

			commit +=1
			insert_local_count=0

		except psycopg2.Error as e:
			logging.info(f"CMTFAIL Commit number: {commit} FAILED with exception: {e}")
			
except KeyboardInterrupt:

	logging.info(f"STOPSCRIPT got interrupt. Didn't commited after item: {p_item}")
	conn.rollback() # rollback hanged inserts if exists
	cur.close()
	conn.close()
	raise SystemExit

except Exception as e:

	logging.error(f"SCRIPTERR got interrupt. Didn't commited after item: {p_item}. Exception: {e}")
	conn.rollback()
	cur.close()
	conn.close()
	raise SystemExit


# At last, when the index reaches the last item, 0, the inserted stories are hanged. Commit those and finish the connection.

try: 
	conn.commit()
	logging.info(f"Last commit successful")
except psycopg2.Error as e:
	logging.info(f"Last commit FAILED with exception: {e}")

# Close connection:
cur.close()
conn.close()
logging.info(f"Database connection closed")



