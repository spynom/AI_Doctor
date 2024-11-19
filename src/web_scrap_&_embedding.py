# Import libraries
from bs4 import BeautifulSoup
import requests
import time
import re
import os
from pathlib import Path
import json
from langchain_core.documents import Document
from uuid import uuid4
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from Logger import get_logger
from UserDefinedFunction import RAGFunctions
from dotenv import load_dotenv
load_dotenv()

logger = get_logger("web_scrap_&_embedding")




def get_headers(url):



    time.sleep(1)
    urls_in_heads = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Firefox/90.0'
    }

    response = requests.get(url,headers=headers)
    if response.status_code == 200:

        soup = BeautifulSoup(response.text, "html.parser")

    else:
        raise print(f"error: {response.status_code}")

    head_collections = soup.findAll("section",class_="topicslist__section")

    for head_collection in head_collections:
        heads = head_collection.findAll("li",class_="topicslist__topiccolumncont-item")
        for head in heads:
            head_url_suffix = head.find('a').get('href')
            urls_in_heads.append( f"https://www.everydayhealth.com{head_url_suffix}" if head_url_suffix.startswith("/") else head_url_suffix)


    return urls_in_heads[::-1]


def get_html(url):
    try_ = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Firefox/90.0'
    }
    while True:

        time.sleep(0.5)
        logger.info(f"current document :  {url}")
        try:
            response = requests.get(url,headers=headers)
        except Exception as e:
            logger.error("error in request %s",e)
            return None

        if response.status_code == 200:
            HTML = BeautifulSoup(response.text, 'html.parser')
            return HTML
        else:

            logger.error(f"error: {response.status_code}")
            time.sleep(5)
            if try_:
                return None
            try_+=1
            continue



def get_docs_from_html(url,html = None):
    if html is None:
        return None

    html1 = html.find("article",
                      class_="eh-template eh-template--article eh-template--rails eh-template--right-rail eh-template--left-rail")

    if html1 is None:
        logger.warning(f"skipped url due to different template found: {url} ")
        return None

    try:
        head = html1.find("div", class_="eh-template__top").find("div",
                                                                 class_="subheader-label eh-pg-headline__subheader").text
    except:
        head = ""
    try:
        title = html1.find("div", class_="eh-template__top").find("h1", class_="eh-pg-headline__title").text
    except:
        return None

    html2 = html1.find("div", class_="eh-template__body")
    if html2 is None:
        logger.warning(f"skipped url no `eh-template__body` class not found in {url} page")
        return None

    contents = html2.findAll("div", class_="eh-widget eh-widget--cb")
    if contents is None:
        logger.warning(f"skipped url : `eh-widget eh-widget--c` class not found in {url} page")
        return None

    documents = []
    links_on_page = []

    for content in contents:
        document = Document(
            page_content=content.text,
            metadata={"source": url,
                      "head": head,
                      "title": title.replace(" ", "_"),
                      },
        )
        documents.append(
            document
        )

        raw_links_data = content.findAll("a")

        if raw_links_data is not None:
            for raw_link in raw_links_data:
                links_on_page.append(raw_link.get('href')) if raw_link.get('href').startswith("https://www.everydayhealth.com") else None


    return documents, links_on_page





def load_documents(urls: list,vector_store, skipped_urls=None, fetched_urls=None) -> None:


    if fetched_urls is None:

        fetched_urls = []
    if skipped_urls is None:
        skipped_urls = []

    links = []
    for url in urls:

        if url in fetched_urls:
            continue

        else:
            fetched_urls.append(url)

        html = get_html(url)
        if html is None:
            continue

        raw_documents = get_docs_from_html(url,html)

        if raw_documents is None:
            continue
        documents,links_on_page = raw_documents
        if links_on_page:
            links.extend(links_on_page)



        uuids = [str(uuid4()) for _ in range(len(documents))]
        vector_store.add_documents(documents=documents, ids=uuids)
        del documents

    if links:
        skipped_urls.extend(load_documents(links,vector_store, skipped_urls, fetched_urls))

        return skipped_urls



if __name__ =="__main__":

    model_name = "all-MiniLM-L6-v2"
    embedding_dim = 384
    cluster_uri =os.getenv("CLUSTER_URL")
    db_name = "langchain"
    collection_name = "vector"

    vector_store = RAGFunctions.vector_store(model_name=model_name,embedding_dim=embedding_dim,cluster_uri=cluster_uri,db_name=db_name,collection_name=collection_name)

    url = "https://www.everydayhealth.com/conditions/"
    logger.info(f"urls of headers are being fetched from {url}....")
    headers = get_headers(url)
    logger.info("urls of headers have been fetched!")

    logger.info(f"documents are being fetched ....")
    load_documents(headers,vector_store)
