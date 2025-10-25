from paper_metadata import search, get_citations

if __name__ == "__main__":
    query = "antioxidants"
    res = search(query)
    
    for i, paper in enumerate(res):
        print(f"[{i+1}] {paper.pdf_url}")