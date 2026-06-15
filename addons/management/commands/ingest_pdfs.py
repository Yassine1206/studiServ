# addons/management/commands/ingest_pdfs.py
# Indexe des fichiers PDF dans le MÊME magasin vectoriel ChromaDB que la FAQ,
# afin que le chatbot puisse répondre à partir de leur contenu.
#
#   python manage.py ingest_pdfs /chemin/vers/dossier_pdfs
#   python manage.py ingest_pdfs fichier1.pdf fichier2.pdf
#
# Dépendances : pip install pypdf langchain langchain-community

import glob
import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Indexe des PDF dans ChromaDB pour le chatbot RAG."

    def add_arguments(self, parser):
        parser.add_argument("paths", nargs="+", help="Fichiers .pdf ou dossiers")
        parser.add_argument("--chunk-size", type=int, default=800)
        parser.add_argument("--chunk-overlap", type=int, default=120)

    def _collect_pdfs(self, paths):
        pdfs = []
        for p in paths:
            if os.path.isdir(p):
                pdfs.extend(glob.glob(os.path.join(p, "**", "*.pdf"), recursive=True))
            elif p.lower().endswith(".pdf"):
                pdfs.append(p)
        return sorted(set(pdfs))

    def handle(self, *args, **opts):
        pdfs = self._collect_pdfs(opts["paths"])
        if not pdfs:
            self.stderr.write(self.style.ERROR("Aucun PDF trouvé."))
            return

        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "Dépendances manquantes : pip install pypdf langchain langchain-community"
            ))
            return

        from chatbot.rag_engine import get_vector_store

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=opts["chunk_size"],
            chunk_overlap=opts["chunk_overlap"],
        )

        all_chunks = []
        for pdf in pdfs:
            self.stdout.write(f"→ Lecture {pdf}")
            try:
                pages = PyPDFLoader(pdf).load()
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"  ignoré ({e})"))
                continue
            chunks = splitter.split_documents(pages)
            for c in chunks:
                c.metadata = {
                    "source": os.path.basename(pdf),
                    "title": os.path.basename(pdf),
                    "category": "pdf",
                    "faq_id": None,
                }
            all_chunks.extend(chunks)

        if not all_chunks:
            self.stderr.write(self.style.ERROR("Aucun contenu extrait."))
            return

        # Ajout au magasin existant (NE recrée PAS la collection : conserve la FAQ).
        vs = get_vector_store()
        vs.add_documents(all_chunks)
        self.stdout.write(self.style.SUCCESS(
            f"{len(all_chunks)} fragments PDF indexés dans ChromaDB "
            f"({len(pdfs)} fichier(s))."
        ))
