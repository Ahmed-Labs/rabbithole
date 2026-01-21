export interface Author {
  name: string;
  authorId?: string;
}

export interface Paper {
  id: string;
  title: string;
  authors: Author[];
  abstract: string;
  year: number | null;
  citationCount: number;
  pdfUrl: string | null;
  url: string;
}
