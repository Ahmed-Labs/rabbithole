from paper_content import search, fetch_pdf_text

if __name__ == "__main__":
    query = "antioxidants"
    res = search(query)
    fetched_pdf = 0

    for paper in res:
        try:
            text = fetch_pdf_text(paper.pdf_url)
            print(f"{paper.title}. Size:{len(text)}")
            fetch_pdf_text += 1
        except:
            pass

    print(f"Fetched {len(res)} papers.")
    print(f"Fetched pdf content for {len(res)} papers.")
