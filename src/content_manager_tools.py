from ast import Break
import os
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fpdf import FPDF
from tavily import TavilyClient
from pydantic import BaseModel, Field, HttpUrl
from agents import function_tool
import sqlite3

# --- Pydantic Models for Data Structuring & Validation ---
class SearchResult(BaseModel):
    """Defines the schema for a single search result from the research tool."""
    title: str = Field(..., description="The title of the search result.")
    url: HttpUrl = Field(..., description="The URL of the search result.")
    content: str = Field(..., description="A summary or snippet of the content.")
    score: Optional[float] = None
    raw_content: Optional[str] = None

class ScrapedArticle(BaseModel):
    """Defines the schema for a scraped article."""
    url: HttpUrl = Field(..., description="The URL of the scraped article.")
    title: str = Field(..., description="The title of the article.")
    scraped_text: str = Field(..., description="The full text content scraped from the article.")

# --- Configuration ---
load_dotenv()

# # --- Agent Tools ---
@function_tool(strict_mode=False)
def research_education_data(query: str, max_results: int = 5) -> Optional[List[SearchResult]]:
    """
    Performs a search for educational data using the Tavily API.
    Returns data structured with the SearchResult Pydantic model.

    Args:
        query: The search query for educational content.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        A list of SearchResult objects or None if an error occurs.
    """

    print("==========================================================")

    print(f"======= Tool Called Search for content ==================")

    print("==========================================================")
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Error: TAVILY_API_KEY environment variable not found.")
        return None

    try:
        tavily = TavilyClient(api_key=api_key)
        response = tavily.search(query=query, search_depth="advanced", max_results=max_results)
        validated_results = [SearchResult(**result) for result in response.get('results', [])]
        return validated_results
    except Exception as e:
        print(f"An error occurred during data research: {e}")
        return None

@function_tool(strict_mode=False)
def scrape_and_structure_data(search_results: List[SearchResult]) -> Optional[List[Dict[str, Any]]]:
    """
    Scrapes textual data from URLs provided by SearchResult objects and structures it.
    Returns a list of dictionaries representing scraped articles.

    Args:
        search_results: List of SearchResult objects containing URLs to scrape.

    Returns:
        A list of dictionaries with article data or None if no data is extracted.
    """
    print("==========================================================")

    print(f"======= Tool Called Scrape Data =========================")

    print("==========================================================")

    if not search_results:
        print("No search results provided to scrape.")
        return None

    scraped_items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for result in search_results:
        try:
            print(f"Scraping: {result.url}")
            response = requests.get(str(result.url), headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            text_content = ' '.join(p.get_text(strip=True) for p in paragraphs)

            scraped_items.append(
                ScrapedArticle(
                    url=result.url,
                    title=result.title,
                    scraped_text=text_content if text_content else "No <p> content found."
                )
            )
        except requests.RequestException as e:
            print(f"Could not scrape {result.url}: {e}")

    if not scraped_items:
        print("Scraping finished, but no data was extracted.")
        return None

    return [item.model_dump() for item in scraped_items]


@function_tool(strict_mode=False)
def save_data(
    data: List[Dict[str, Any]],
    filename: str,
    save_format: str = 'csv',
    db_name: str = '/content/education_data.db',  # <--- IMPORTANT: Explicit Path!
    table_name: str = 'articles'
) -> None:
    """
    Saves the structured data to a specified format (CSV, Excel, PDF, or SQLite).
    """

    print("==========================================================")

    print(f"======= Tool Called Saving Data into a {save_format} or Database ===========================")

    print("==========================================================")

    if not data:
        print("Data is empty. Nothing to save.")
        return

    df = pd.DataFrame(data)

    # Explicitly cast 'url' to string *if* it exists
    if 'url' in df.columns:
        df['url'] = df['url'].astype(str)

    try:
        if 'url' in df.columns:
            df['url'] = df['url'].astype(str)

        match save_format:
            case 'csv':
                df.to_csv(f"{filename}.csv", index=False, encoding='utf-8-sig')
                print(f"Data successfully saved to {filename}.csv")
            case 'excel':
                df.to_excel(f"{filename}.xlsx", index=False, engine='openpyxl')
                print(f"Data successfully saved to {filename}.xlsx")
            case 'sqlite':
                conn = None
                try:
                    conn = sqlite3.connect(db_name)
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    print(f"Data successfully saved to table '{table_name}' in '{db_name}'")
                except Exception as e:
                    print(f"An error occurred writing to the database: {e}")
                    raise  # Re-raise so the error isn't swallowed
                finally:
                    if conn:
                        conn.close()
                
            case 'pdf':
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for _, row in df.iterrows():
                    title = str(row['title']).encode('latin-1', 'replace').decode('latin-1')
                    url_str = str(row['url']).encode('latin-1', 'replace').decode('latin-1')
                    text = str(row['scraped_text']).encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_font("Arial", 'B', 12)
                    pdf.multi_cell(0, 10, f"Title: {title}")
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 10, f"URL: {url_str}")
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 5, text)
                    pdf.ln(10)
                pdf.output(f"{filename}.pdf")
                print(f"Data successfully saved to {filename}.pdf")
            case _:
                print(f"Error: Unsupported save format '{save_format}'.")
    except Exception as e:
        print(f"An error occurred while saving the data: {e}")



@function_tool()
def search_database(
    query: str,
    db_name: str = 'education_data.db',
    table_name: str = 'articles'
) -> Optional[List[Dict[str, Any]]]:
    """
    Searches the SQLite database for a query string in 'title' or 'scraped_text'.

    Args:
        query: The search query to match in the database.
        db_name: Name of the SQLite database file.
        table_name: Name of the table to search

    Returns:
        A list of dictionaries with matching records or None if no results.
    """

    print("==========================================================")

    print(f"======= Tool Called Search for content in Database ====================")

    print("==========================================================")
    if not os.path.exists(db_name):
        print(f"Error: Database '{db_name}' not found.")
        return None
    try:
        conn = sqlite3.connect(db_name)
        sql_query = f"SELECT * FROM {table_name} WHERE title LIKE ? OR scraped_text LIKE ?"
        search_term = f"%{query}%"
        results_df = pd.read_sql_query(sql_query, conn, params=(search_term, search_term))
        conn.close()
        return results_df.to_dict('records') if not results_df.empty else None
    except Exception as e:
        print(f"An error occurred while searching the database: {e}")
        return None