from mcp.server.fastmcp import FastMCP
import sqlite3
import os

# Get the absolute path to the database file in the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "community.db")

mcp = FastMCP("Community Chatters")

@mcp.tool()
def get_top_chatters():
    """Retrieve the top chatters sorted by number of messages."""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute the query to fetch chatters sorted by messages
        cursor.execute("SELECT name, messages FROM chatters ORDER BY messages DESC")
        results = cursor.fetchall()
        conn.close()

        # Format the results as a list of dictionaries
        chatters = [{"name": name, "messages": messages} for name, messages in results]
        return chatters

    except Exception as e:
        return {"error": str(e)}


# Run the MCP server locally
if __name__ == '__main__':
    print(f"Using database at: {DB_PATH}")  # Optional debug print
    mcp.run()

    